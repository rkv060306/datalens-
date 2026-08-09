from fastapi import APIRouter, HTTPException, Depends
from backend.models.analysis import MLTrainRequest, CompareRequest
from backend.services.db_service import db_service
from backend.services.file_service import file_service
from backend.services.profiling_service import profiling_service
from backend.services.statistics_service import statistics_service
from backend.services.insight_service import insight_service
from backend.services.ml_service import ml_service
from backend.services.media_service import media_service
from backend.utils.auth import get_current_user_payload

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

async def _get_ds_df(dataset_id: str, user: dict):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized.")
    
    if ds["fileCategory"] != "tabular":
        return ds, None
    df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])
    return ds, df

@router.get("/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        return {"fileCategory": ds["fileCategory"], "message": "Non-tabular media dataset."}
    return profiling_service.profile_dataframe(df)

@router.get("/{dataset_id}/statistics")
async def get_dataset_statistics(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        raise HTTPException(status_code=400, detail="Statistics available for tabular CSV/Excel files only.")
    return statistics_service.calculate_statistics(df)

@router.get("/{dataset_id}/correlation")
async def get_dataset_correlation(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        raise HTTPException(status_code=400, detail="Correlation available for tabular CSV/Excel files only.")
    return statistics_service.calculate_correlation(df)

@router.get("/{dataset_id}/outliers")
async def get_dataset_outliers(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        raise HTTPException(status_code=400, detail="Outlier detection available for tabular files only.")
    return statistics_service.detect_outliers(df)

@router.get("/{dataset_id}/insights")
async def get_dataset_insights(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        return []
    return insight_service.generate_insights(df)

@router.post("/{dataset_id}/ml")
async def run_machine_learning(
    dataset_id: str,
    req: MLTrainRequest,
    user: dict = Depends(get_current_user_payload)
):
    ds, df = await _get_ds_df(dataset_id, user)
    if df is None:
        raise HTTPException(status_code=400, detail="Machine Learning requires a tabular dataset.")

    return ml_service.train_model(
        df=df,
        target_col=req.targetColumn,
        feature_cols=req.featureColumns,
        model_type=req.modelType,
        n_clusters=req.nClusters or 3
    )

@router.post("/compare")
async def compare_datasets(
    req: CompareRequest,
    user: dict = Depends(get_current_user_payload)
):
    dsA, dfA = await _get_ds_df(req.datasetIdA, user)
    dsB, dfB = await _get_ds_df(req.datasetIdB, user)

    if dfA is None or dfB is None:
        raise HTTPException(status_code=400, detail="Dataset comparison is available for tabular datasets.")

    profileA = profiling_service.profile_dataframe(dfA)
    profileB = profiling_service.profile_dataframe(dfB)

    statsA = statistics_service.calculate_statistics(dfA)
    statsB = statistics_service.calculate_statistics(dfB)

    return {
        "datasetA": {
            "info": dsA,
            "profile": profileA,
            "stats": statsA
        },
        "datasetB": {
            "info": dsB,
            "profile": profileB,
            "stats": statsB
        },
        "comparisonSummary": {
            "rowDelta": profileB["rows"] - profileA["rows"],
            "columnDelta": profileB["columns"] - profileA["columns"],
            "qualityScoreDelta": round(profileB["qualityScore"] - profileA["qualityScore"], 1),
            "missingPctDelta": round(profileB["missingPercentage"] - profileA["missingPercentage"], 2)
        }
    }

@router.get("/media/{dataset_id}")
async def get_media_analytics(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    cat = ds["fileCategory"]
    if cat == "image":
        return media_service.analyze_image(ds["filePath"])
    elif cat == "video":
        return media_service.analyze_video(ds["filePath"])
    else:
        raise HTTPException(status_code=400, detail="Requested dataset is not an image or video file.")
