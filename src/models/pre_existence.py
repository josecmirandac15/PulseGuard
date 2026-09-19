from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class PreExistence(Base):
    __tablename__ = "pre_existences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(20), ForeignKey("patients.patient_id"), nullable=False)
    condition_name = Column(String(100), nullable=False)
    diagnosed_date = Column(Date, nullable=True)
    severity = Column(String(20), nullable=True)  # mild, moderate, severe
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", backref="pre_existences")
