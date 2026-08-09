import pandas as pd
import numpy as np
from typing import Dict, Any, List
from backend.services.statistics_service import statistics_service
from backend.services.profiling_service import profiling_service

class InsightService:
    @staticmethod
    def generate_insights(df: pd.DataFrame) -> List[Dict[str, Any]]:
        insights = []
        profile = profiling_service.profile_dataframe(df)
        stats = statistics_service.calculate_statistics(df)
        corr = statistics_service.calculate_correlation(df)
        outliers = statistics_service.detect_outliers(df)

        # 1. Missing Data Warning
        missing_pct = profile["missingPercentage"]
        if missing_pct > 10.0:
            insights.append({
                "id": "missing-data-high",
                "type": "warning",
                "category": "Data Quality",
                "title": "High Missing Data Concentration",
                "description": f"{missing_pct}% of total cells in this dataset are missing or unrecorded.",
                "explanation": f"Calculated as (missing_cells / total_cells) * 100 = {missing_pct}%. Missing values can distort statistical models and charts.",
                "metric": f"{missing_pct}% Missing"
            })
        elif missing_pct > 0:
            insights.append({
                "id": "missing-data-low",
                "type": "info",
                "category": "Data Quality",
                "title": "Minor Missing Values Detected",
                "description": f"{missing_pct}% missing values found. Consider using the Data Cleaning module to impute mean/median.",
                "explanation": f"Total missing cells: {profile['missingCells']}.",
                "metric": f"{missing_pct}% Missing"
            })

        # 2. Duplicate Rows Warning
        dups = profile["duplicateRows"]
        if dups > 0:
            dup_pct = round((dups / profile["rows"]) * 100, 2)
            insights.append({
                "id": "duplicates-detected",
                "type": "warning",
                "category": "Data Integrity",
                "title": f"Duplicate Records Found",
                "description": f"{dups} duplicate rows detected ({dup_pct}% of total dataset).",
                "explanation": "Identified exact identical row matches across all columns. You can purge them in the Data Cleaning tab.",
                "metric": f"{dups} Row Duplicates"
            })

        # 3. High Correlation Insights
        for sc in corr.get("strongCorrelations", []):
            insights.append({
                "id": f"corr-{sc['column1']}-{sc['column2']}",
                "type": "positive" if sc["correlation"] > 0 else "info",
                "category": "Correlation",
                "title": f"Strong Relationship: {sc['column1']} & {sc['column2']}",
                "description": f"{sc['column1']} shows a {sc['relationship']} correlation of r = {sc['correlation']} with {sc['column2']}.",
                "explanation": sc["explanation"],
                "metric": f"r = {sc['correlation']}"
            })

        # 4. Outlier Risk Warnings
        for col_name, outlier_info in outliers.get("outlierColumns", {}).items():
            pct = outlier_info["outlierPercentage"]
            if pct > 3.0:
                insights.append({
                    "id": f"outlier-{col_name}",
                    "type": "anomaly",
                    "category": "Outlier Detection",
                    "title": f"Extreme Values in '{col_name}'",
                    "description": f"{outlier_info['iqrOutlierCount']} potential outliers ({pct}%) detected outside IQR bounds [{outlier_info['lowerBound']} to {outlier_info['upperBound']}].",
                    "explanation": f"Identified using 1.5 * Interquartile Range (IQR = Q3 - Q1). Sample outliers: {outlier_info['sampleOutliers'][:4]}",
                    "metric": f"{outlier_info['iqrOutlierCount']} Outliers"
                })

        # 5. Dominant Category Concentration
        for cat_col, c_stat in stats.get("categorical", {}).items():
            top_pct = c_stat.get("topCategoryPercentage", 0)
            if top_pct >= 40.0 and c_stat.get("uniqueCount", 0) > 1:
                insights.append({
                    "id": f"dominant-{cat_col}",
                    "type": "info",
                    "category": "Distribution",
                    "title": f"Dominant Category in '{cat_col}'",
                    "description": f"Category '{c_stat['topCategory']}' dominates {cat_col} with {top_pct}% of total records.",
                    "explanation": f"Frequency count: {c_stat['topCategoryFrequency']} out of {c_stat['count']} total records.",
                    "metric": f"{top_pct}% Share"
                })

        # 6. Trend / Time-Series Insights
        date_cols = [col for col, p in profile["columnProfiles"].items() if p["detectedType"] == "datetime"]
        num_cols = list(stats.get("numeric", {}).keys())
        
        if date_cols and num_cols:
            date_col = date_cols[0]
            val_col = num_cols[0]
            try:
                ts_df = df.copy()
                ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors='coerce')
                ts_df = ts_df.dropna(subset=[date_col, val_col]).sort_values(by=date_col)
                if len(ts_df) >= 4:
                    start_val = ts_df[val_col].iloc[:3].mean()
                    end_val = ts_df[val_col].iloc[-3:].mean()
                    if start_val > 0:
                        growth_pct = round(((end_val - start_val) / start_val) * 100, 2)
                        direction = "increased" if growth_pct > 0 else "decreased"
                        insights.append({
                            "id": f"trend-{date_col}-{val_col}",
                            "type": "positive" if growth_pct > 0 else "warning",
                            "category": "Trend Analysis",
                            "title": f"Time-Series Growth Trend",
                            "description": f"Over the analyzed timeframe, '{val_col}' {direction} by {abs(growth_pct)}%.",
                            "explanation": f"Compared initial average ({start_val:.2f}) against recent average ({end_val:.2f}) over column '{date_col}'.",
                            "metric": f"{growth_pct:+.1f}% Growth"
                        })
            except Exception:
                pass

        # 7. General Dataset Summary Insight
        insights.append({
            "id": "dataset-health-summary",
            "type": "positive" if profile["qualityScore"] >= 75 else "warning",
            "category": "Overview",
            "title": f"Overall Dataset Quality Rating: {profile['qualityScore']}/100",
            "description": profile["qualityBreakdown"]["status"],
            "explanation": " ".join(profile["qualityBreakdown"]["reasons"]),
            "metric": f"{profile['qualityScore']} / 100"
        })

        return insights

insight_service = InsightService()
