"""
Upload routes — /api/upload
"""
import os
import shutil
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.orm_models import UploadedFile, Dataset
from backend.schemas.schemas import UploadResponse
from backend.services.dataset_service import dataset_service
from backend.agents.cleaning_agent import cleaning_agent

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use CSV or Excel.")

    # Save file
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Persist uploaded_files record
    db_file = UploadedFile(filename=file.filename, file_path=dest_path)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Load and auto-clean
    df = dataset_service._read_file(dest_path)
    cleaned_df, _ = cleaning_agent.run(df)

    # Persist dataset metadata
    db_dataset = Dataset(
        dataset_name=file.filename,
        file_id=db_file.id,
        rows=len(cleaned_df),
        columns=len(cleaned_df.columns),
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    # Cache cleaned DataFrame
    dataset_service.cache(db_dataset.id, cleaned_df)

    return UploadResponse(
        file_id=db_file.id,
        dataset_id=db_dataset.id,
        filename=file.filename,
        rows=len(cleaned_df),
        columns=len(cleaned_df.columns),
        upload_time=db_file.upload_time,
    )


@router.get("/list")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        {"id": d.id, "name": d.dataset_name, "rows": d.rows,
         "columns": d.columns, "created_at": d.created_at}
        for d in datasets
    ]
