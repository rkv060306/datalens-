import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List
from fastapi import HTTPException
from backend.config import SAMPLES_DIR

class FileService:
    @staticmethod
    def read_dataset_df(file_path: str, file_type: str) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset file not found: {file_path}")

        ext = file_type.lower()
        try:
            if ext == "csv":
                try:
                    df = pd.read_csv(path)
                except UnicodeDecodeError:
                    df = pd.read_csv(path, encoding="latin-1")
            elif ext in ["xlsx", "xls"]:
                df = pd.read_excel(path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
            
            # Clean column names
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {path.name}: {str(e)}")

    @staticmethod
    def save_dataframe(df: pd.DataFrame, target_path: Path):
        ext = target_path.suffix.lower()
        if ext == ".csv":
            df.to_csv(target_path, index=False)
        elif ext in [".xlsx", ".xls"]:
            df.to_excel(target_path, index=False)
        else:
            df.to_csv(target_path, index=False)

    @staticmethod
    def get_paginated_preview(
        df: pd.DataFrame, 
        page: int = 1, 
        page_size: int = 50, 
        search: str = "", 
        sort_by: str = "", 
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        
        preview_df = df.copy()

        # Search filtering
        if search:
            search_str = search.lower()
            mask = preview_df.astype(str).apply(lambda row: row.str.lower().str.contains(search_str).any(), axis=1)
            preview_df = preview_df[mask]

        # Sorting
        if sort_by and sort_by in preview_df.columns:
            ascending = (sort_order.lower() != "desc")
            preview_df = preview_df.sort_values(by=sort_by, ascending=ascending)

        total_rows = len(preview_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)

        page_df = preview_df.iloc[start_idx:end_idx]
        
        cleaned_records = []
        for row in page_df.to_dict(orient="records"):
            cleaned_row = {}
            for k, v in row.items():
                if pd.isna(v) or (isinstance(v, float) and (np.isinf(v) or np.isnan(v))):
                    cleaned_row[k] = None
                else:
                    cleaned_row[k] = str(v) if isinstance(v, (pd.Timestamp, pd.Timedelta)) else v
            cleaned_records.append(cleaned_row)

        return {
            "records": cleaned_records,
            "columns": list(df.columns),
            "page": page,
            "pageSize": page_size,
            "totalRows": total_rows,
            "totalPages": total_pages
        }

    @staticmethod
    def get_sample_files() -> List[Dict[str, Any]]:
        samples = []
        if SAMPLES_DIR.exists():
            for f in SAMPLES_DIR.glob("*.csv"):
                samples.append({
                    "fileName": f.name,
                    "filePath": str(f),
                    "name": f.stem.replace("_", " ").title(),
                    "fileType": "csv"
                })
        return samples

file_service = FileService()
