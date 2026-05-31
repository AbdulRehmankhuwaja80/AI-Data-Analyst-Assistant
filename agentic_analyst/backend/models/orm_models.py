"""
ORM Models — maps to MySQL tables
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from backend.database.connection import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id          = Column(Integer, primary_key=True, index=True)
    filename    = Column(String(255), nullable=False)
    file_path   = Column(String(500), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)


class Dataset(Base):
    __tablename__ = "datasets"

    id           = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(255), nullable=False)
    file_id      = Column(Integer, nullable=True)          # FK → uploaded_files.id
    rows         = Column(BigInteger, default=0)
    columns      = Column(Integer, default=0)
    created_at   = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id         = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=True)
    user_query = Column(Text, nullable=False)
    agent_used = Column(String(100), nullable=True)
    response   = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id          = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(255), nullable=False)
    report_path = Column(String(500), nullable=False)
    dataset_id  = Column(Integer, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
