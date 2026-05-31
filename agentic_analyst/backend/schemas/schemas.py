"""
Pydantic schemas — request/response validation
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    file_id:     int
    dataset_id:  int
    filename:    str
    rows:        int
    columns:     int
    upload_time: datetime

    class Config:
        from_attributes = True


# ── Query ────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    dataset_id: int
    question:   str = Field(..., min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    agent_used:   str
    sql:          Optional[str] = None
    result_data:  Optional[List[Dict[str, Any]]] = None
    chart_json:   Optional[str] = None
    insights:     Optional[List[str]] = None
    answer:       str


# ── Profiling ────────────────────────────────────────────────────────────────

class ProfilingResponse(BaseModel):
    dataset_id:   int
    row_count:    int
    column_count: int
    columns:      List[Dict[str, Any]]   # per-column stats
    correlations: Optional[Dict[str, Any]] = None


# ── Cleaning ─────────────────────────────────────────────────────────────────

class CleaningResponse(BaseModel):
    dataset_id:      int
    missing_fixed:   int
    duplicates_removed: int
    columns_converted: int
    outliers_flagged: int
    summary:         List[str]


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role:    str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    dataset_id: int
    messages:   List[ChatMessage]


class ChatResponse(BaseModel):
    reply:      str
    agent_used: str
    chart_json: Optional[str] = None
    sql:        Optional[str] = None


# ── Report ────────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    report_id:   int
    report_name: str
    download_url: str
