"""Report route — /api/report"""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.orm_models import GeneratedReport
from backend.schemas.schemas import ReportResponse
from backend.services.dataset_service import dataset_service
from backend.agents.profiling_agent import profiling_agent
from backend.agents.cleaning_agent import cleaning_agent
from backend.agents.insight_agent import insight_agent
from backend.agents.report_agent import report_agent

router = APIRouter()

class ReportRequest(BaseModel):
    dataset_id: int
    question: Optional[str] = "Generate a comprehensive analysis report"

@router.post("/generate", response_model=ReportResponse)
def generate_report(req: ReportRequest, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(req.dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))

    profiling = profiling_agent.run(df)
    _, cleaning = cleaning_agent.run(df)
    insight_result = insight_agent.run(req.question, df)

    report_path = report_agent.generate(
        dataset_name=f"dataset_{req.dataset_id}",
        df=df,
        profiling=profiling,
        cleaning=cleaning,
        insights=insight_result.get("insights", []),
    )

    report_name = os.path.basename(report_path)
    db_report = GeneratedReport(
        report_name=report_name,
        report_path=report_path,
        dataset_id=req.dataset_id,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return ReportResponse(
        report_id=db_report.id,
        report_name=report_name,
        download_url=f"/reports/{report_name}",
    )

@router.get("/list")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(GeneratedReport).order_by(GeneratedReport.created_at.desc()).all()
    return [
        {"id": r.id, "name": r.report_name,
         "download_url": f"/reports/{r.report_name}",
         "created_at": r.created_at}
        for r in reports
    ]
