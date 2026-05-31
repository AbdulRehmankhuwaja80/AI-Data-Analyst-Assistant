"""Clean route — /api/clean"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.schemas.schemas import CleaningResponse
from backend.services.dataset_service import dataset_service
from backend.agents.cleaning_agent import cleaning_agent

router = APIRouter()

@router.post("/{dataset_id}", response_model=CleaningResponse)
def clean_dataset(dataset_id: int, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))

    cleaned_df, report = cleaning_agent.run(df)
    dataset_service.cache(dataset_id, cleaned_df)

    return CleaningResponse(
        dataset_id=dataset_id,
        missing_fixed=report["missing_fixed"],
        duplicates_removed=report["duplicates_removed"],
        columns_converted=report["columns_converted"],
        outliers_flagged=report["outliers_flagged"],
        summary=report["summary"],
    )
