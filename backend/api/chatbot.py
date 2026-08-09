from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.services.db_service import db_service
from backend.services.file_service import file_service
from backend.services.chatbot_service import chatbot_service
from backend.utils.auth import get_current_user_payload

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

class ChatbotQueryRequest(BaseModel):
    datasetId: str
    message: str
    provider: str = "builtin"  # "builtin", "gemini", "groq", "openrouter", "huggingface"
    apiKey: str | None = None
    model: str | None = None

@router.post("/query")
async def query_chatbot(
    req: ChatbotQueryRequest,
    user: dict = Depends(get_current_user_payload)
):
    if not req.datasetId:
        raise HTTPException(status_code=400, detail="datasetId is required")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    ds = await db_service.get_dataset_by_id(req.datasetId)
    if not ds or (ds["userId"] != user["id"] and ds["userId"] != "guest-user-0000-0000-0000"):
        raise HTTPException(status_code=404, detail="Dataset not found or unauthorized access.")

    df = None
    if ds.get("fileCategory") == "tabular":
        df = file_service.read_dataset_df(ds["filePath"], ds["fileType"])

    return chatbot_service.query(
        dataset_info=ds, 
        df=df, 
        user_message=req.message, 
        provider=req.provider, 
        api_key=req.apiKey, 
        model=req.model
    )
