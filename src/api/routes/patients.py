from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models import Patient, Policy

router = APIRouter()


@router.get("/patients")
async def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).order_by(Patient.patient_id).all()
    policies = {p.patient_id: p.policy_number for p in db.query(Policy).all()}
    return {
        "total": len(patients),
        "patients": [
            {
                "patient_id": pt.patient_id,
                "name": pt.name,
                "age": pt.age,
                "gender": pt.gender,
                "policy_number": policies.get(pt.patient_id),
            }
            for pt in patients
        ],
    }
