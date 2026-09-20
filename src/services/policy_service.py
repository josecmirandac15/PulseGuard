from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional

from src.models import Policy, Patient, PreExistence


class PolicyService:
    def __init__(self, db: Session):
        self.db = db

    def get_policy_by_number(self, policy_number: str) -> Optional[Policy]:
        return self.db.query(Policy).filter(Policy.policy_number == policy_number).first()

    def get_policy_by_id(self, policy_id: str) -> Optional[Policy]:
        return self.db.query(Policy).filter(Policy.policy_id == policy_id).first()

    def validate_policy(self, policy: Policy) -> dict:
        today = date.today()

        if policy.status == "cancelled":
            return {"valid": False, "reason": "cancelada"}
        
        if policy.status == "suspended":
            return {"valid": False, "reason": "suspendida"}
        
        if policy.status == "expired":
            return {"valid": False, "reason": "expirada"}
        
        if policy.end_date < today:
            return {"valid": False, "reason": "expirada"}
        
        if policy.start_date > today:
            return {"valid": False, "reason": "aún no vigente"}
        
        if policy.status == "active":
            return {"valid": True, "reason": "vigente"}
        
        return {"valid": False, "reason": "con estado desconocido"}

    def check_coverage(self, policy: Policy, amount: float) -> dict:
        if policy.max_coverage_amount and amount > policy.max_coverage_amount:
            return {
                "covered": False,
                "reason": f"Amount ${amount} exceeds max coverage ${policy.max_coverage_amount}",
                "max_coverage": policy.max_coverage_amount
            }
        
        return {
            "covered": True,
            "reason": "Within coverage limits",
            "max_coverage": policy.max_coverage_amount
        }

    def get_patient_by_policy(self, policy: Policy) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.patient_id == policy.patient_id).first()
