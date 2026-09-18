from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PreExistence(BaseModel):
    condition: str
    diagnosed_date: Optional[str] = None
    severity: Optional[str] = None


class Patient(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    blood_type: Optional[str] = None
    allergies: List[str] = []
    pre_existences: List[PreExistence] = []


class Policy(BaseModel):
    policy_id: str
    patient_id: str
    policy_number: str
    status: PolicyStatus
    start_date: str
    end_date: str
    coverage_type: str
    max_coverage_amount: float
    provider: str


class EmergencyAdmission(BaseModel):
    admission_id: str
    patient_id: str
    policy_number: str
    timestamp: datetime
    admission_reason: str
    vital_signs: Optional[dict] = None
    symptoms: List[str] = []
    hospital_code: str


class Alert(BaseModel):
    alert_id: str
    admission_id: str
    level: AlertLevel
    message: str
    recommendations: List[str] = []
    agent_analysis: str
    created_at: datetime


class AuditLog(BaseModel):
    log_id: str
    admission_id: str
    agent_action: str
    details: dict
    timestamp: datetime
