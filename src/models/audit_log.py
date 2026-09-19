from sqlalchemy import Column, String, DateTime, JSON, Integer
from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    admission_id = Column(String(30), nullable=True)
    action = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)
