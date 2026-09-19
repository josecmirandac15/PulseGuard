from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.base import get_db
from src.models import Admission, Alert

router = APIRouter()


@router.get("/alerts")
async def get_alerts(
    level: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    
    if level:
        query = query.filter(Alert.level == level)
    
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": query.count(),
        "alerts": [
            {
                "alert_id": a.alert_id,
                "admission_id": a.admission_id,
                "level": a.level,
                "message": a.message,
                "recommendations": a.recommendations,
                "agent_analysis": a.agent_analysis,
                "ai_report": a.ai_report,
                "hospital_notified": a.hospital_notified,
                "insurer_notified": a.insurer_notified,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in alerts
        ]
    }


@router.get("/alerts/stats")
async def get_alerts_stats(db: Session = Depends(get_db)):
    alerts_by_level = db.query(
        Alert.level,
        func.count(Alert.alert_id)
    ).group_by(Alert.level).all()

    total_admissions = db.query(Admission).count()
    total_alerts = db.query(Alert).count()
    
    today_admissions = db.query(Admission).filter(
        func.date(Admission.timestamp) == func.current_date()
    ).count()

    return {
        "total_admissions": total_admissions,
        "today_admissions": today_admissions,
        "total_alerts": total_alerts,
        "alerts_by_level": {level: count for level, count in alerts_by_level}
    }
