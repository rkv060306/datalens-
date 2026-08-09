from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ChartRecommendation(BaseModel):
    id: str
    title: str
    chartType: str  # histogram, scatter, bar, line, box, heatmap, pie, area
    xAxis: Optional[str] = None
    yAxis: Optional[str] = None
    color: Optional[str] = None
    aggregation: Optional[str] = "none"
    plotlyData: Dict[str, Any]

class InsightItem(BaseModel):
    id: str
    type: str  # warning, info, positive, anomaly
    category: str
    title: str
    description: str
    explanation: str
    metric: Optional[str] = None

class MLTrainRequest(BaseModel):
    targetColumn: str
    featureColumns: List[str]
    modelType: str  # linear_regression, random_forest, clustering
    nClusters: Optional[int] = 3

class MLResultResponse(BaseModel):
    isSuitable: bool
    message: str
    modelType: str
    targetColumn: Optional[str] = None
    metrics: Dict[str, Any] = {}
    featureImportance: Dict[str, float] = {}
    predictionsSample: List[Dict[str, Any]] = []

class CompareRequest(BaseModel):
    datasetIdA: str
    datasetIdB: str
