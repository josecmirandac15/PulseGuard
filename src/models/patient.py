from sqlalchemy import Column, String, Integer, Date, JSON
from .base import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_type = Column(String(5), nullable=True)
    allergies = Column(JSON, default=list)
