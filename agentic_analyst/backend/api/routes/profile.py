"""Profile route — /api/profile"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services.dataset_service import dataset_service
from backend.agents.profiling_agent import profiling_agent

router = APIRouter()

@router.get("/{dataset_id}")
def get_profile(dataset_id: int, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))
    return profiling_agent.run(df)
