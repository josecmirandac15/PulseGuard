from fastapi import APIRouter
from src.api.routes import admissions, alerts, dashboard, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admissions.router, tags=["admissions"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(ws.router, tags=["realtime"])
