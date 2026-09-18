import json
import os
from typing import Optional, List
from ..agent.models import Policy, Patient, PolicyStatus


class PolicyService:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
        self.policies = self._load_policies()
        self.patients = self._load_patients()

    def _load_policies(self) -> dict:
        filepath = os.path.join(self.data_dir, "policies.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                return {p["policy_number"]: Policy(**p) for p in data}
        return {}

    def _load_patients(self) -> dict:
        filepath = os.path.join(self.data_dir, "patients.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                return {p["patient_id"]: Patient(**p) for p in data}
        return {}

    def get_policy(self, policy_number: str) -> Optional[Policy]:
        return self.policies.get(policy_number)

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self.patients.get(patient_id)

    def validate_policy(self, policy: Policy) -> dict:
        from datetime import datetime
        now = datetime.now()
        end_date = datetime.fromisoformat(policy.end_date)

        if policy.status == PolicyStatus.CANCELLED:
            return {"valid": False, "reason": "Policy cancelled"}
        elif policy.status == PolicyStatus.SUSPENDED:
            return {"valid": False, "reason": "Policy suspended"}
        elif now > end_date:
            return {"valid": False, "reason": "Policy expired"}
        elif policy.status == PolicyStatus.ACTIVE:
            return {"valid": True, "reason": "Policy active and valid"}

        return {"valid": False, "reason": "Unknown policy status"}

    def check_pre_existences(self, patient: Patient, admission_reason: str) -> dict:
        relevant_pre_existences = []
        
        cardiac_keywords = ["chest", "heart", "cardiac", "angina", "infarction", "arrhythmia", "hypertension", "blood pressure"]
        respiratory_keywords = ["breath", "respiratory", "lung", "pulmonary", "asthma", "copd", "dyspnea"]
        metabolic_keywords = ["diabetes", "glucose", "metabolic", "kidney", "renal"]
        
        admission_lower = admission_reason.lower()
        
        for pre_ex in patient.pre_existences:
            condition_lower = pre_ex.condition.lower()
            is_relevant = False
            
            if any(kw in admission_lower for kw in cardiac_keywords):
                if any(kw in condition_lower for kw in ["heart", "cardiac", "coronary", "hypertension", "artery"]):
                    is_relevant = True
            
            if any(kw in admission_lower for kw in respiratory_keywords):
                if any(kw in condition_lower for kw in ["asthma", "copd", "respiratory", "lung", "pulmonary"]):
                    is_relevant = True
            
            if any(kw in admission_lower for kw in metabolic_keywords):
                if any(kw in condition_lower for kw in ["diabetes", "kidney", "renal"]):
                    is_relevant = True
            
            if not is_relevant:
                condition_words = set(condition_lower.split())
                reason_words = set(admission_lower.split())
                if condition_words & reason_words:
                    is_relevant = True
            
            if is_relevant:
                relevant_pre_existences.append(pre_ex)

        return {
            "has_relevant_pre_existences": len(relevant_pre_existences) > 0,
            "pre_existences": relevant_pre_existences,
            "requires_review": len(relevant_pre_existences) > 0
        }
