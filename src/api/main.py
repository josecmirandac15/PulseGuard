from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from src.models.base import engine, Base
from src.api.routes import api_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="PulseGuard API",
    description="Emergency Admission Alert System - hackIAthon Panamá 2026",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "PulseGuard API v2.0",
        "hackathon": "hackIAthon Panamá 2026",
        "reto": "Sistema de Alerta Temprana de Ingresos a Emergencias",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    from sqlalchemy import text
    from src.models.base import SessionLocal

    db_status = "disconnected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "PulseGuard API",
        "version": "2.0.0",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development")
    }
