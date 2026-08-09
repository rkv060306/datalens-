import pandas as pd
import numpy as np
from typing import Dict, Any, List

class StatisticsService:
    @staticmethod
    def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        numeric_stats = {}
        categorical_stats = {}

        for col in df.columns:
            series = df[col].dropna()
            if series.empty:
                continue

            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                count = int(series.count())
                mean_val = float(series.mean())
                std_val = float(series.std()) if count > 1 else 0.0
                min_val = float(series.min())
                max_val = float(series.max())
                median_val = float(series.median())
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                var_val = float(series.var()) if count > 1 else 0.0
                
                mode_series = series.mode()
                mode_val = float(mode_series[0]) if not mode_series.empty else mean_val

                numeric_stats[col] = {
                    "count": count,
                    "mean": round(mean_val, 3),
                    "median": round(median_val, 3),
                    "mode": round(mode_val, 3),
                    "std": round(std_val, 3),
                    "variance": round(var_val, 3),
                    "min": round(min_val, 3),
                    "max": round(max_val, 3),
                    "range": round(max_val - min_val, 3),
                    "q1": round(q1, 3),
                    "q3": round(q3, 3),
                    "iqr": round(iqr, 3),
                    "skewness": round(float(series.skew()), 3) if count > 2 else 0.0
                }
            else:
                total_cnt = len(series)
                unique_cnt = int(series.nunique())
                val_counts = series.value_counts().head(10).to_dict()

                top_cat = list(val_counts.keys())[0] if val_counts else "N/A"
                top_freq = list(val_counts.values())[0] if val_counts else 0
                top_pct = round((top_freq / total_cnt) * 100, 2) if total_cnt > 0 else 0.0

                distribution = [
                    {"category": str(k), "count": int(v), "percentage": round((int(v)/total_cnt)*100, 2)}
                    for k, v in val_counts.items()
                ]

                categorical_stats[col] = {
                    "count": total_cnt,
                    "uniqueCount": unique_cnt,
                    "topCategory": str(top_cat),
                    "topCategoryFrequency": top_freq,
                    "topCategoryPercentage": top_pct,
                    "distribution": distribution
                }

        return {
            "numeric": numeric_stats,
            "categorical": categorical_stats
        }

    @staticmethod
    def calculate_correlation(df: pd.DataFrame) -> Dict[str, Any]:
        num_df = df.select_dtypes(include=[np.number])
        if num_df.shape[1] < 2:
            return {
                "columns": list(num_df.columns),
                "matrix": [],
                "strongCorrelations": [],
                "message": "At least 2 numeric columns are required to compute correlation matrix."
            }

        corr_matrix = num_df.corr(method="pearson").round(3)
        cols = list(corr_matrix.columns)
        
        matrix_rows = []
        strong_correlations = []

        for i, col1 in enumerate(cols):
            row_vals = []
            for j, col2 in enumerate(cols):
                val = float(corr_matrix.iloc[i, j])
                val = 0.0 if np.isnan(val) else val
                row_vals.append(val)

                if i < j:
                    if abs(val) >= 0.65:
                        relationship = "strong positive" if val > 0 else "strong negative"
                        strong_correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": val,
                            "relationship": relationship,
                            "explanation": f"As {col1} {'increases' if val > 0 else 'increases'}, {col2} tends to {'increase' if val > 0 else 'decrease'} (r = {val:.2f})."
                        })
            matrix_rows.append(row_vals)

        return {
            "columns": cols,
            "matrix": matrix_rows,
            "strongCorrelations": strong_correlations,
            "message": f"Calculated Pearson correlation across {len(cols)} numeric features."
        }

    @staticmethod
    def detect_outliers(df: pd.DataFrame) -> Dict[str, Any]:
        outlier_summary = {}

        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue

            # IQR Method
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            iqr_outliers = series[(series < lower_bound) | (series > upper_bound)]

            # Z-Score Method
            mean_val, std_val = series.mean(), series.std()
            z_scores = (series - mean_val) / std_val if std_val > 0 else pd.Series(0, index=series.index)
            z_outliers = series[z_scores.abs() > 3.0]

            if len(iqr_outliers) > 0 or len(z_outliers) > 0:
                outlier_summary[col] = {
                    "column": col,
                    "iqrOutlierCount": len(iqr_outliers),
                    "zScoreOutlierCount": len(z_outliers),
                    "lowerBound": round(float(lower_bound), 2),
                    "upperBound": round(float(upper_bound), 2),
                    "sampleOutliers": [round(float(v), 2) for v in iqr_outliers.head(10).tolist()],
                    "outlierPercentage": round((len(iqr_outliers) / len(df)) * 100, 2)
                }

        return {
            "outlierColumns": outlier_summary,
            "totalOutlierColumnsCount": len(outlier_summary)
        }

statistics_service = StatisticsService()
