import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class ProfilingService:
    @staticmethod
    def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        total_rows, total_cols = df.shape
        if total_rows == 0 or total_cols == 0:
            return {
                "rows": total_rows,
                "columns": total_cols,
                "memoryUsageMB": 0.0,
                "duplicateRows": 0,
                "missingCells": 0,
                "missingPercentage": 0.0,
                "columnProfiles": {},
                "columnTypesSummary": {"numeric": 0, "categorical": 0, "datetime": 0, "boolean": 0},
                "qualityScore": 0.0,
                "qualityBreakdown": {"status": "Empty Dataset", "reasons": ["Dataset contains no rows or columns"]}
            }

        memory_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3)
        duplicate_rows = int(df.duplicated().sum())
        total_cells = total_rows * total_cols
        missing_cells = int(df.isna().sum().sum())
        missing_percentage = round((missing_cells / total_cells) * 100, 2)

        column_profiles = {}
        type_counts = {"numeric": 0, "categorical": 0, "datetime": 0, "boolean": 0}

        for col in df.columns:
            series = df[col]
            missing_cnt = int(series.isna().sum())
            missing_pct = round((missing_cnt / total_rows) * 100, 2)
            unique_cnt = int(series.nunique(dropna=True))
            
            # Detect Data Type
            detected_type = ProfilingService._detect_column_type(series)
            
            if detected_type in ["integer", "float"]:
                type_counts["numeric"] += 1
            elif detected_type == "datetime":
                type_counts["datetime"] += 1
            elif detected_type == "boolean":
                type_counts["boolean"] += 1
            else:
                type_counts["categorical"] += 1

            column_profiles[col] = {
                "name": col,
                "detectedType": detected_type,
                "missingCount": missing_cnt,
                "missingPercentage": missing_pct,
                "uniqueCount": unique_cnt,
                "sampleValues": [str(x) for x in series.dropna().iloc[:3].tolist()]
            }

        # Calculate Data Quality Score (0 - 100)
        quality_score, quality_breakdown = ProfilingService._calculate_quality_score(
            total_rows, total_cols, duplicate_rows, missing_cells, total_cells, column_profiles, df
        )

        return {
            "rows": total_rows,
            "columns": total_cols,
            "memoryUsageMB": memory_usage_mb,
            "duplicateRows": duplicate_rows,
            "missingCells": missing_cells,
            "missingPercentage": missing_percentage,
            "columnProfiles": column_profiles,
            "columnTypesSummary": type_counts,
            "qualityScore": quality_score,
            "qualityBreakdown": quality_breakdown
        }

    @staticmethod
    def _detect_column_type(series: pd.Series) -> str:
        # Check boolean
        non_nulls = series.dropna()
        if len(non_nulls) == 0:
            return "string"

        if pd.api.types.is_bool_dtype(series):
            return "boolean"

        # Check numeric
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return "integer"
            return "float"

        # Try parsing dates if string
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            # Sample check for date format
            sample = non_nulls.head(20).astype(str)
            date_matches = 0
            for val in sample:
                if len(val) >= 6:
                    try:
                        pd.to_datetime(val, errors='raise')
                        date_matches += 1
                    except Exception:
                        pass
            if date_matches / len(sample) > 0.8:
                return "datetime"

            # Check if high repetition / low unique count -> categorical
            if series.nunique() / len(series) < 0.5:
                return "categorical"

        return "string"

    @staticmethod
    def _calculate_quality_score(
        rows: int, cols: int, duplicates: int, missing_cells: int, total_cells: int, profiles: dict, df: pd.DataFrame
    ) -> Tuple[float, Dict[str, Any]]:
        score = 100.0
        reasons = []

        # 1. Missing values penalty (up to 30 points)
        missing_pct = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        missing_penalty = min(30.0, missing_pct * 1.5)
        score -= missing_penalty
        if missing_penalty > 0:
            reasons.append(f"-{missing_penalty:.1f} pts: {missing_pct:.1f}% missing values across dataset.")

        # 2. Duplicate rows penalty (up to 20 points)
        dup_pct = (duplicates / rows) * 100 if rows > 0 else 0
        dup_penalty = min(20.0, dup_pct * 2.0)
        score -= dup_penalty
        if dup_penalty > 0:
            reasons.append(f"-{dup_penalty:.1f} pts: {duplicates} duplicate rows ({dup_pct:.1f}% of total).")

        # 3. Empty columns penalty (up to 20 points)
        empty_cols = sum(1 for p in profiles.values() if p["missingPercentage"] == 100.0)
        if empty_cols > 0:
            empty_penalty = min(20.0, empty_cols * 5.0)
            score -= empty_penalty
            reasons.append(f"-{empty_penalty:.1f} pts: {empty_cols} completely empty column(s).")

        # 4. Outliers penalty for numeric columns (up to 15 points)
        numeric_cols = [c for c, p in profiles.items() if p["detectedType"] in ["integer", "float"]]
        total_outliers = 0
        for nc in numeric_cols:
            s = df[nc].dropna()
            if len(s) > 4:
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    outliers = ((s < (q1 - 1.5 * iqr)) | (s > (q3 + 1.5 * iqr))).sum()
                    total_outliers += outliers

        if total_outliers > 0:
            outlier_penalty = min(15.0, (total_outliers / rows) * 10.0)
            score -= outlier_penalty
            reasons.append(f"-{outlier_penalty:.1f} pts: {total_outliers} statistical outliers detected.")

        score = max(0.0, min(100.0, round(score, 1)))
        
        status = "Excellent Dataset" if score >= 90 else "Good Dataset" if score >= 75 else "Moderate Dataset" if score >= 50 else "Poor Dataset"
        
        if not reasons:
            reasons.append("No data quality defects detected. Perfect dataset!")

        return score, {"status": status, "reasons": reasons}

profiling_service = ProfilingService()
