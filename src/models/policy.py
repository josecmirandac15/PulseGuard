from sqlalchemy import Column, String, Date, Numeric
from .base import Base


class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(String(20), primary_key=True)
    patient_id = Column(String(20), nullable=False)
    policy_number = Column(String(30), unique=True, nullable=False)
    status = Column(String(20), nullable=False)  # active, expired, suspended, cancelled
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    coverage_type = Column(String(30), nullable=True)
    max_coverage_amount = Column(Numeric(12, 2), nullable=True)
    provider = Column(String(100), nullable=True)
