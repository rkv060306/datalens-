import sys
from pathlib import Path

# Add project root directory to sys.path so 'backend' package imports resolve correctly
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import BASE_DIR
from backend.services.db_service import db_service
from backend.api import auth, datasets, analytics, visualization, reports, chatbot

app = FastAPI(
    title="DataLens — Universal Online Data Analytics Platform API",
    description="Backend API for automated data profiling, quality scoring, statistical analysis, Plotly visualizations, ML, and PDF report exports.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(visualization.router)
app.include_router(reports.router)
app.include_router(chatbot.router)

# Mount Frontend static files
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")

@app.on_event("startup")
async def startup_db_client():
    await db_service.connect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

