"""
Dataset Service — DataFrame loading, caching, and persistence
"""
import logging
import os
from typing import Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.models.orm_models import UploadedFile, Dataset

logger = logging.getLogger(__name__)

# In-process cache: dataset_id → DataFrame
_df_cache: dict[int, pd.DataFrame] = {}


class DatasetService:

    def load(self, dataset_id: int, db: Session) -> pd.DataFrame:
        """Load DataFrame for dataset_id, using cache if available."""
        if dataset_id in _df_cache:
            return _df_cache[dataset_id]

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        uploaded = db.query(UploadedFile).filter(
            UploadedFile.id == dataset.file_id
        ).first()
        if not uploaded or not os.path.exists(uploaded.file_path):
            raise FileNotFoundError(f"File not found for dataset {dataset_id}")

        df = self._read_file(uploaded.file_path)
        _df_cache[dataset_id] = df
        logger.info("Loaded dataset %d — %d rows, %d cols", dataset_id, len(df), len(df.columns))
        return df

    def cache(self, dataset_id: int, df: pd.DataFrame) -> None:
        _df_cache[dataset_id] = df

    def evict(self, dataset_id: int) -> None:
        _df_cache.pop(dataset_id, None)

    @staticmethod
    def _read_file(path: str) -> pd.DataFrame:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(path)
        raise ValueError(f"Unsupported file type: {ext}")


dataset_service = DatasetService()
