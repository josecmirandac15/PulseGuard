from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EmergencyAdmission(BaseModel):
    admission_id: str = Field(..., example="ADM-20260919-001")
    patient_id: str = Field(..., example="PAT-001")
    policy_number: str = Field(..., example="POL-2024-001")
    timestamp: datetime
    admission_reason: str = Field(..., example="Dolor torácico agudo")
    vital_signs: Optional[dict] = Field(None, example={
        "heart_rate": 95,
        "blood_pressure": "140/90",
        "oxygen_saturation": 94
    })
    symptoms: List[str] = Field(default=[], example=["dolor pecho", "disnea"])
    hospital_code: str = Field(..., example="HOSP-001")


class AdmissionResponse(BaseModel):
    admission_id: str
    status: str
    alert_level: str
    message: str
    ai_report: Optional[str] = None
    hospital_notified: bool = False
    insurer_notified: bool = False
