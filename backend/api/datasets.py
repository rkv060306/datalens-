import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from backend.config import UPLOADS_DIR
from backend.models.dataset import DatasetCleanRequest
from backend.services.db_service import db_service
from backend.services.file_service import file_service
from backend.services.profiling_service import profiling_service
from backend.services.cleaning_service import cleaning_service
from backend.utils.auth import get_current_user_payload
from backend.utils.validators import validate_uploaded_file, sanitize_filename, get_file_type_category

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    user: dict = Depends(get_current_user_payload)
):
    ext = validate_uploaded_file(file)
    cat = get_file_type_category(ext)
    
    clean_name = sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{clean_name}"
    target_path = UPLOADS_DIR / unique_filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = target_path.stat().st_size

    rows, cols, quality_score = 0, 0, 100.0

    if cat == "tabular":
        try:
            df = file_service.read_dataset_df(str(target_path), ext)
            rows, cols = df.shape
            profile = profiling_service.profile_dataframe(df)
            quality_score = profile["qualityScore"]
        except Exception as e:
            target_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"Failed to parse uploaded dataset: {str(e)}")

    dataset_dict = {
        "userId": user["id"],
        "name": name or clean_name.rsplit(".", 1)[0].replace("_", " ").title(),
        "fileName": unique_filename,
        "filePath": str(target_path),
        "fileType": ext,
        "fileCategory": cat,
        "rows": rows,
        "columns": cols,
        "fileSize": file_size,
        "qualityScore": quality_score,
        "isSample": False
    }

    created = await db_service.create_dataset(dataset_dict)
    return created

@router.get("")
async def list_datasets(user: dict = Depends(get_current_user_payload)):
    return await db_service.get_datasets_by_user(user["id"])

@router.get("/samples")
async def list_sample_datasets():
    return file_service.get_sample_files()

@router.post("/samples/load")
async def load_sample_dataset(
    fileName: str = Form(...),
    user: dict = Depends(get_current_user_payload)
):
    samples = file_service.get_sample_files()
    matched = next((s for s in samples if s["fileName"] == fileName), None)
    if not matched:
        raise HTTPException(status_code=4404, detail="Sample dataset not found.")

    src_path = Path(matched["filePath"])
    ext = matched["fileType"]
    clean_name = matched["fileName"]
    unique_filename = f"sample_{uuid.uuid4().hex}_{clean_name}"
    target_path = UPLOADS_DIR / unique_filename

    shutil.copyfile(src_path, target_path)

    df = file_service.read_dataset_df(str(target_path), ext)
    rows, cols = df.shape
    profile = profiling_service.profile_dataframe(df)

    dataset_dict = {
        "userId": user["id"],
        "name": matched["name"],
        "fileName": unique_filename,
        "filePath": str(target_path),
        "fileType": ext,
        "fileCategory": "tabular",
        "rows": rows,
        "columns": cols,
        "fileSize": target_path.stat().st_size,
        "qualityScore": profile["qualityScore"],
        "isSample": True
    }

    return await db_service.create_dataset(dataset_dict)

@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
    search: str = Query(""),
    sortBy: str = Query(""),
    sortOrder: str = Query("asc"),
    user: dict = Depends(get_current_user_payload)
):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized access.")

    preview_data = None
    if ds["fileCategory"] == "tabular":
        df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])
        preview_data = file_service.get_paginated_preview(
            df, page=page, page_size=pageSize, search=search, sort_by=sortBy, sort_order=sortOrder
        )

    return {
        "dataset": ds,
        "preview": preview_data
    }

@router.post("/{dataset_id}/clean")
async def clean_dataset(
    dataset_id: str,
    clean_req: DatasetCleanRequest,
    user: dict = Depends(get_current_user_payload)
):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if ds["fileCategory"] != "tabular":
        raise HTTPException(status_code=400, detail="Data cleaning is only applicable to tabular CSV/Excel files.")

    df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])

    cleaned_df, report = cleaning_service.clean_dataframe(
        df,
        missing_strategy=clean_req.missingStrategy,
        custom_values=clean_req.customValues,
        remove_duplicates=clean_req.removeDuplicates,
        normalize_categories=clean_req.normalizeCategories,
        type_overrides=clean_req.typeOverrides
    )

    # Save to new cleaned file copy
    clean_filename = f"cleaned_{uuid.uuid4().hex}_{ds['fileName']}"
    clean_path = UPLOADS_DIR / clean_filename
    file_service.save_dataframe(cleaned_df, clean_path)

    cleaned_ds_dict = {
        "userId": user["id"],
        "name": f"{ds['name']} (Cleaned)",
        "fileName": clean_filename,
        "filePath": str(clean_path),
        "fileType": ds["fileType"],
        "fileCategory": "tabular",
        "rows": len(cleaned_df),
        "columns": len(cleaned_df.columns),
        "fileSize": clean_path.stat().st_size,
        "qualityScore": report["newQualityScore"],
        "isSample": False
    }

    created_ds = await db_service.create_dataset(cleaned_ds_dict)
    return {
        "cleanedDataset": created_ds,
        "cleaningReport": report
    }

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user: dict = Depends(get_current_user_payload)
):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    # Remove physical file
    Path(ds["filePath"]).unlink(missing_ok=True)
    await db_service.delete_dataset(dataset_id, ds["userId"])
    return {"message": "Dataset deleted successfully."}
