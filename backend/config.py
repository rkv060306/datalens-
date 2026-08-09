import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Storage Paths
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "generated_reports"
SAMPLES_DIR = BASE_DIR / "samples"
DATA_DIR = BASE_DIR / "data_store"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Security & Auth
SECRET_KEY = os.getenv("SECRET_KEY", "datalens-super-secret-jwt-key-2026-analytics-platform")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days token

# Database Settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "datalens_db")

# Upload Limits & Extension validation
MAX_FILE_SIZE_MB = 100
ALLOWED_EXTENSIONS = {
    # Structured Data
    "csv", "xlsx", "xls",
    # Images
    "jpg", "jpeg", "png", "webp", "bmp", "tiff",
    # Videos
    "mp4", "avi", "mov", "mkv", "webm"
}
