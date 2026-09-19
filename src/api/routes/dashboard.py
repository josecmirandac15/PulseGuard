from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.base import get_db
from src.models import Admission, Alert

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_admissions = db.query(Admission).count()

    today = func.date(Admission.timestamp)
    admissions_today = db.query(Admission).filter(
        func.date(Admission.timestamp) == func.current_date()
    ).count()

    alerts_by_level = db.query(
        Alert.level,
        func.count(Alert.alert_id)
    ).group_by(Alert.level).all()

    return {
        "total_admissions": total_admissions,
        "admissions_today": admissions_today,
        "alerts_by_level": {level: count for level, count in alerts_by_level},
        "total_alerts": db.query(Alert).count()
    }
