from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from backend.services.db_service import db_service
from backend.services.file_service import file_service
from backend.services.visualization_service import visualization_service
from backend.utils.auth import get_current_user_payload

router = APIRouter(prefix="/api/visualizations", tags=["Visualizations"])

class CustomChartRequest(BaseModel):
    datasetId: str
    chartType: str
    xAxis: Optional[str] = None
    yAxis: Optional[str] = None
    color: Optional[str] = None
    aggregation: Optional[str] = "none"

@router.get("/{dataset_id}/recommendations")
async def get_chart_recommendations(dataset_id: str, user: dict = Depends(get_current_user_payload)):
    ds = await db_service.get_dataset_by_id(dataset_id)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if ds["fileCategory"] != "tabular":
        return []

    df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])
    return visualization_service.get_auto_recommendations(df)

@router.post("/generate")
async def generate_custom_visualization(
    req: CustomChartRequest,
    user: dict = Depends(get_current_user_payload)
):
    ds = await db_service.get_dataset_by_id(req.datasetId)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if ds["fileCategory"] != "tabular":
        raise HTTPException(status_code=400, detail="Custom visualizations are supported for tabular datasets.")

    df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])
    
    return visualization_service.generate_custom_chart(
        df=df,
        chart_type=req.chartType,
        x_axis=req.xAxis,
        y_axis=req.yAxis,
        color_col=req.color,
        aggregation=req.aggregation or "none"
    )
