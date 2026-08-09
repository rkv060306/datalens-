from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class DatasetCreate(BaseModel):
    name: str
    fileName: str
    filePath: str
    fileType: str
    fileCategory: str  # tabular, image, video
    rows: int = 0
    columns: int = 0
    fileSize: int = 0
    qualityScore: float = 0.0
    isSample: bool = False

class DatasetResponse(BaseModel):
    id: str
    userId: str
    name: str
    fileName: str
    filePath: str
    fileType: str
    fileCategory: str
    rows: int
    columns: int
    fileSize: int
    qualityScore: float
    isSample: bool
    createdAt: str

class DatasetCleanRequest(BaseModel):
    missingStrategy: Optional[Dict[str, str]] = None  # col -> mean|median|mode|remove_rows|custom
    customValues: Optional[Dict[str, Any]] = None
    removeDuplicates: bool = False
    normalizeCategories: Optional[List[str]] = None
    typeOverrides: Optional[Dict[str, str]] = None
