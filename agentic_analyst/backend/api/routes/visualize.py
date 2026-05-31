"""Visualize route — /api/visualize"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.services.dataset_service import dataset_service
from backend.agents.visualization_agent import visualization_agent

router = APIRouter()

class VizRequest(BaseModel):
    dataset_id: int
    question: str

@router.post("/")
def create_chart(req: VizRequest, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(req.dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))
    return visualization_agent.run(req.question, df)
