from sqlalchemy import Column, String, DateTime, JSON
from .base import Base


class Admission(Base):
    __tablename__ = "admissions"

    admission_id = Column(String(30), primary_key=True)
    patient_id = Column(String(20), nullable=False)
    policy_number = Column(String(30), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    admission_reason = Column(String(500), nullable=False)
    vital_signs = Column(JSON, nullable=True)
    symptoms = Column(JSON, default=list)
    hospital_code = Column(String(20), nullable=True)
    status = Column(String(20), default="received")
