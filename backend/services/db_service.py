import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import MONGODB_URL, DATABASE_NAME, DATA_DIR

class DatabaseService:
    def __init__(self):
        self.use_mongo = False
        self.client = None
        self.db = None
        
        # Local JSON File store fallback paths
        self.users_file = DATA_DIR / "users.json"
        self.datasets_file = DATA_DIR / "datasets.json"
        self.analyses_file = DATA_DIR / "analyses.json"
        self._init_file_store()

    def _init_file_store(self):
        for file_path in [self.users_file, self.datasets_file, self.analyses_file]:
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([], f)

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=1500)
            # Test ping
            await self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self.use_mongo = True
            print("Successfully connected to MongoDB database!")
        except Exception as e:
            self.use_mongo = False
            print(f"MongoDB not available ({e}). Using persistent JSON File Store fallback.")

    # File store helpers
    def _read_file(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_file(self, file_path: Path, data: List[Dict[str, Any]]):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _clean_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if doc is None:
            return None
        doc = dict(doc)
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    # USER OPERATIONS
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_data["id"] = user_data.get("id") or str(uuid.uuid4())
        user_data["createdAt"] = user_data.get("createdAt") or datetime.utcnow().isoformat()
        
        if self.use_mongo:
            doc = user_data.copy()
            await self.db.users.insert_one(doc)
            return self._clean_doc(doc)
        else:
            users = self._read_file(self.users_file)
            users.append(user_data)
            self._write_file(self.users_file, users)
            return user_data

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            doc = await self.db.users.find_one({"email": email})
            return self._clean_doc(doc)
        else:
            users = self._read_file(self.users_file)
            for u in users:
                if u.get("email") == email:
                    return u
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            doc = await self.db.users.find_one({"id": user_id})
            return self._clean_doc(doc)
        else:
            users = self._read_file(self.users_file)
            for u in users:
                if u.get("id") == user_id:
                    return u
            return None

    # DATASET OPERATIONS
    async def create_dataset(self, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        dataset_data["id"] = dataset_data.get("id") or str(uuid.uuid4())
        dataset_data["createdAt"] = dataset_data.get("createdAt") or datetime.utcnow().isoformat()
        
        if self.use_mongo:
            doc = dataset_data.copy()
            await self.db.datasets.insert_one(doc)
            return self._clean_doc(doc)
        else:
            datasets = self._read_file(self.datasets_file)
            datasets.append(dataset_data)
            self._write_file(self.datasets_file, datasets)
            return dataset_data

    async def get_datasets_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        if self.use_mongo:
            cursor = self.db.datasets.find({"userId": user_id})
            raw_list = await cursor.to_list(length=500)
            return [self._clean_doc(d) for d in raw_list]
        else:
            datasets = self._read_file(self.datasets_file)
            return [d for d in datasets if d.get("userId") == user_id]

    async def get_dataset_by_id(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            doc = await self.db.datasets.find_one({"id": dataset_id})
            return self._clean_doc(doc)
        else:
            datasets = self._read_file(self.datasets_file)
            for d in datasets:
                if d.get("id") == dataset_id:
                    return d
            return None

    async def update_dataset(self, dataset_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            await self.db.datasets.update_one({"id": dataset_id}, {"$set": updates})
            return await self.get_dataset_by_id(dataset_id)
        else:
            datasets = self._read_file(self.datasets_file)
            for d in datasets:
                if d.get("id") == dataset_id:
                    d.update(updates)
                    self._write_file(self.datasets_file, datasets)
                    return d
            return None

    async def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        if self.use_mongo:
            res = await self.db.datasets.delete_one({"id": dataset_id, "userId": user_id})
            return res.deleted_count > 0
        else:
            datasets = self._read_file(self.datasets_file)
            initial_count = len(datasets)
            filtered = [d for d in datasets if not (d.get("id") == dataset_id and d.get("userId") == user_id)]
            if len(filtered) < initial_count:
                self._write_file(self.datasets_file, filtered)
                return True
            return False

    # ANALYSIS OPERATIONS
    async def save_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis_data["id"] = analysis_data.get("id") or str(uuid.uuid4())
        analysis_data["createdAt"] = analysis_data.get("createdAt") or datetime.utcnow().isoformat()
        
        if self.use_mongo:
            await self.db.analyses.update_one(
                {"datasetId": analysis_data["datasetId"]},
                {"$set": analysis_data},
                upsert=True
            )
            return analysis_data
        else:
            analyses = self._read_file(self.analyses_file)
            existing_idx = None
            for idx, a in enumerate(analyses):
                if a.get("datasetId") == analysis_data["datasetId"]:
                    existing_idx = idx
                    break
            if existing_idx is not None:
                analyses[existing_idx] = analysis_data
            else:
                analyses.append(analysis_data)
            self._write_file(self.analyses_file, analyses)
            return analysis_data

    async def get_analysis_by_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        if self.use_mongo:
            return await self.db.analyses.find_one({"datasetId": dataset_id})
        else:
            analyses = self._read_file(self.analyses_file)
            for a in analyses:
                if a.get("datasetId") == dataset_id:
                    return a
            return None

db_service = DatabaseService()
