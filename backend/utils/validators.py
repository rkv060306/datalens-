import os
from pathlib import Path
from fastapi import HTTPException, UploadFile
from backend.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

def validate_uploaded_file(file: UploadFile) -> str:
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext

def sanitize_filename(filename: str) -> str:
    cleaned = "".join(c for c in filename if c.isalnum() or c in ("-", "_", "."))
    return cleaned or "dataset"

def get_file_type_category(ext: str) -> str:
    ext = ext.lower()
    if ext in {"csv", "xlsx", "xls"}:
        return "tabular"
    elif ext in {"jpg", "jpeg", "png", "webp", "bmp", "tiff"}:
        return "image"
    elif ext in {"mp4", "avi", "mov", "mkv", "webm"}:
        return "video"
    return "unknown"
