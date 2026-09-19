from sqlalchemy.orm import Session
from typing import Optional, List

from src.models import Patient, PreExistence


class PatientService:
    def __init__(self, db: Session):
        self.db = db

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.patient_id == patient_id).first()

    def get_pre_existences(self, patient_id: str) -> List[PreExistence]:
        return self.db.query(PreExistence).filter(
            PreExistence.patient_id == patient_id
        ).all()

    def check_pre_existences(self, patient_id: str, admission_reason: str) -> dict:
        pre_existences = self.get_pre_existences(patient_id)
        
        relevant = []
        admission_lower = admission_reason.lower()
        
        cardiac_keywords = ["chest", "heart", "cardiac", "angina", "infarction", "arrhythmia", "hypertension"]
        respiratory_keywords = ["breath", "respiratory", "lung", "pulmonary", "asthma", "copd", "dyspnea"]
        metabolic_keywords = ["diabetes", "glucose", "metabolic", "kidney", "renal"]
        
        for pre_ex in pre_existences:
            condition_lower = pre_ex.condition_name.lower()
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
                relevant.append(pre_ex)

        return {
            "has_relevant": len(relevant) > 0,
            "relevant_conditions": [
                {
                    "condition": p.condition_name,
                    "severity": p.severity,
                    "notes": p.notes
                }
                for p in relevant
            ],
            "total_pre_existences": len(pre_existences)
        }

    def get_allergies(self, patient_id: str) -> List[str]:
        patient = self.get_patient(patient_id)
        if patient and patient.allergies:
            return patient.allergies
        return []
