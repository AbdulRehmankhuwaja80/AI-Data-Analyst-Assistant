"""
Agentic AI Data Analyst — FastAPI Backend Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import upload, query, profile, clean, visualize, report, chat
from backend.database.connection import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating DB tables...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Agentic AI Data Analyst",
    version="1.0.0",
    description="Multi-agent AI system for natural language data analysis",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/reports", StaticFiles(directory="reports"), name="reports")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(upload.router,    prefix="/api/upload",    tags=["Upload"])
app.include_router(query.router,     prefix="/api/query",     tags=["Query"])
app.include_router(profile.router,   prefix="/api/profile",   tags=["Profile"])
app.include_router(clean.router,     prefix="/api/clean",     tags=["Cleaning"])
app.include_router(visualize.router, prefix="/api/visualize", tags=["Visualization"])
app.include_router(report.router,    prefix="/api/report",    tags=["Reports"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "agentic-analyst"}
