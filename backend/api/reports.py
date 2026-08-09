from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.config import REPORTS_DIR
from backend.services.db_service import db_service
from backend.services.file_service import file_service
from backend.services.report_service import report_service
from backend.utils.auth import get_current_user_payload

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class ReportGenerateRequest(BaseModel):
    datasetId: str

@router.post("/generate")
async def generate_report(
    req: ReportGenerateRequest,
    user: dict = Depends(get_current_user_payload)
):
    ds = await db_service.get_dataset_by_id(req.datasetId)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if ds["fileCategory"] != "tabular":
        raise HTTPException(status_code=400, detail="PDF report generation is available for tabular datasets.")

    df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])
    pdf_path = report_service.generate_pdf_report(ds["name"], df)

    return {
        "reportName": pdf_path.name,
        "downloadUrl": f"/api/reports/download/{pdf_path.name}"
    }

@router.get("/download/{filename}")
async def download_report_file(filename: str):
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf" if filename.endswith(".pdf") else "application/octet-stream"
    )
