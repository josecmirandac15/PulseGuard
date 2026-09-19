from sqlalchemy import Column, String, DateTime, JSON, Boolean, Text
from .base import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(36), primary_key=True)
    admission_id = Column(String(30), nullable=False)
    level = Column(String(20), nullable=False)  # info, warning, critical
    message = Column(String(500), nullable=False)
    recommendations = Column(JSON, default=list)
    agent_analysis = Column(Text, nullable=True)
    ai_report = Column(Text, nullable=True)
    hospital_notified = Column(Boolean, default=False)
    insurer_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
