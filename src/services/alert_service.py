from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import uuid

from src.models import Alert, Admission


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        admission_id: str,
        level: str,
        message: str,
        recommendations: list = None,
        agent_analysis: str = None,
        ai_report: str = None
    ) -> Alert:
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            admission_id=admission_id,
            level=level,
            message=message,
            recommendations=recommendations or [],
            agent_analysis=agent_analysis,
            ai_report=ai_report,
            created_at=datetime.utcnow()
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def update_alert_notifications(
        self,
        alert_id: str,
        hospital_notified: bool = False,
        insurer_notified: bool = False
    ) -> Optional[Alert]:
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.hospital_notified = hospital_notified
            alert.insurer_notified = insurer_notified
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def get_alerts_by_admission(self, admission_id: str):
        return self.db.query(Alert).filter(Alert.admission_id == admission_id).all()

    def get_alerts_by_level(self, level: str):
        return self.db.query(Alert).filter(Alert.level == level).all()

    def get_recent_alerts(self, limit: int = 10):
        return self.db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
