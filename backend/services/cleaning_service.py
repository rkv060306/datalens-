import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from backend.services.profiling_service import profiling_service

class CleaningService:
    @staticmethod
    def clean_dataframe(
        df: pd.DataFrame,
        missing_strategy: Optional[Dict[str, str]] = None,
        custom_values: Optional[Dict[str, Any]] = None,
        remove_duplicates: bool = False,
        normalize_categories: Optional[List[str]] = None,
        type_overrides: Optional[Dict[str, str]] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        
        cleaned_df = df.copy()
        report_log = []

        # 1. Type overrides
        if type_overrides:
            for col, new_type in type_overrides.items():
                if col in cleaned_df.columns:
                    try:
                        if new_type in ["integer", "int"]:
                            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0).astype(int)
                        elif new_type in ["float"]:
                            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').astype(float)
                        elif new_type in ["datetime", "date"]:
                            cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                        elif new_type in ["categorical", "string", "str"]:
                            cleaned_df[col] = cleaned_df[col].astype(str)
                        report_log.append(f"Converted column '{col}' to type '{new_type}'.")
                    except Exception as e:
                        report_log.append(f"Failed to convert '{col}' to '{new_type}': {str(e)}")

        # 2. Remove duplicates
        if remove_duplicates:
            before_cnt = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            removed_cnt = before_cnt - len(cleaned_df)
            if removed_cnt > 0:
                report_log.append(f"Removed {removed_cnt} duplicate rows.")

        # 3. Normalize categories
        if normalize_categories:
            for col in normalize_categories:
                if col in cleaned_df.columns:
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.title()
                    report_log.append(f"Normalized string casing for column '{col}'.")

        # 4. Handle Missing Values
        if missing_strategy:
            for col, strategy in missing_strategy.items():
                if col in cleaned_df.columns:
                    missing_cnt = cleaned_df[col].isna().sum()
                    if missing_cnt == 0:
                        continue

                    if strategy == "remove_rows":
                        cleaned_df = cleaned_df.dropna(subset=[col])
                        report_log.append(f"Removed {missing_cnt} rows with missing values in '{col}'.")
                    elif strategy == "mean" and pd.api.types.is_numeric_dtype(cleaned_df[col]):
                        mean_val = cleaned_df[col].mean()
                        cleaned_df[col] = cleaned_df[col].fillna(mean_val)
                        report_log.append(f"Filled missing values in '{col}' with mean ({mean_val:.2f}).")
                    elif strategy == "median" and pd.api.types.is_numeric_dtype(cleaned_df[col]):
                        median_val = cleaned_df[col].median()
                        cleaned_df[col] = cleaned_df[col].fillna(median_val)
                        report_log.append(f"Filled missing values in '{col}' with median ({median_val:.2f}).")
                    elif strategy == "mode":
                        mode_series = cleaned_df[col].mode()
                        if not mode_series.empty:
                            mode_val = mode_series[0]
                            cleaned_df[col] = cleaned_df[col].fillna(mode_val)
                            report_log.append(f"Filled missing values in '{col}' with mode ('{mode_val}').")
                    elif strategy == "custom" and custom_values and col in custom_values:
                        c_val = custom_values[col]
                        cleaned_df[col] = cleaned_df[col].fillna(c_val)
                        report_log.append(f"Filled missing values in '{col}' with custom value '{c_val}'.")

        # Re-profile cleaned dataframe
        new_profile = profiling_service.profile_dataframe(cleaned_df)

        return cleaned_df, {
            "appliedOperations": report_log,
            "newQualityScore": new_profile["qualityScore"],
            "newRows": new_profile["rows"],
            "newColumns": new_profile["columns"],
            "newMissingPercentage": new_profile["missingPercentage"]
        }

cleaning_service = CleaningService()
