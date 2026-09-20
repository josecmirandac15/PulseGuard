from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette.concurrency import run_in_threadpool
from datetime import datetime
import time

from src.models.base import get_db
from src.models import Admission, Alert, AuditLog
from src.api.schemas.admission import EmergencyAdmission, AdmissionResponse
from src.agent.engine import EmergencyAlertAgent
from src.core.realtime import manager

router = APIRouter()

agent = EmergencyAlertAgent()


async def _broadcast_admission(db: Session, admission: EmergencyAdmission, result: dict):
    """Emite la admisión procesada al panel en tiempo real."""
    try:
        stats_rows = db.query(
            Alert.level, func.count(Alert.alert_id)
        ).group_by(Alert.level).all()
        payload = {
            "admission_id": result["admission_id"],
            "patient_id": admission.patient_id,
            "patient_name": result.get("patient_name", "Unknown"),
            "policy_number": admission.policy_number,
            "admission_reason": admission.admission_reason,
            "hospital_code": admission.hospital_code,
            "timestamp": admission.timestamp.isoformat(),
            "alert": {
                "level": result["alert_level"],
                "message": result["message"],
                "recommendations": result.get("recommendations", []),
                "ai_report": result.get("ai_report"),
            },
            "hospital_notified": result.get("hospital_notified", False),
            "insurer_notified": result.get("insurer_notified", False),
            "stats": {
                "total_admissions": db.query(Admission).count(),
                "total_alerts": db.query(Alert).count(),
                "alerts_by_level": {level: count for level, count in stats_rows},
            },
        }
        await manager.broadcast("admission.processed", payload)
    except Exception:
        pass


@router.post("/webhook/admission", response_model=AdmissionResponse)
async def receive_admission(admission: EmergencyAdmission, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        admission_record = Admission(
            admission_id=admission.admission_id,
            patient_id=admission.patient_id,
            policy_number=admission.policy_number,
            timestamp=admission.timestamp,
            admission_reason=admission.admission_reason,
            vital_signs=admission.vital_signs,
            symptoms=admission.symptoms,
            hospital_code=admission.hospital_code,
            status="received"
        )
        db.add(admission_record)
        db.commit()

        result = await run_in_threadpool(
            agent.process_admission, admission.model_dump(mode="json")
        )

        await _broadcast_admission(db, admission, result)

        processing_time = (time.time() - start_time) * 1000

        return AdmissionResponse(
            admission_id=result["admission_id"],
            status=result["status"],
            alert_level=result["alert_level"],
            message=result["message"],
            ai_report=result.get("ai_report"),
            hospital_notified=result.get("hospital_notified", False),
            insurer_notified=result.get("insurer_notified", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admissions")
async def get_admissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    admissions = db.query(Admission).offset(skip).limit(limit).all()
    return {
        "total": db.query(Admission).count(),
        "admissions": [
            {
                "admission_id": a.admission_id,
                "patient_id": a.patient_id,
                "policy_number": a.policy_number,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "admission_reason": a.admission_reason,
                "symptoms": a.symptoms,
                "hospital_code": a.hospital_code,
                "status": a.status
            }
            for a in admissions
        ]
    }


@router.get("/admissions/{admission_id}")
async def get_admission(admission_id: str, db: Session = Depends(get_db)):
    admission = db.query(Admission).filter(Admission.admission_id == admission_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")

    alerts = db.query(Alert).filter(Alert.admission_id == admission_id).all()

    return {
        "admission": {
            "admission_id": admission.admission_id,
            "patient_id": admission.patient_id,
            "policy_number": admission.policy_number,
            "timestamp": admission.timestamp.isoformat() if admission.timestamp else None,
            "admission_reason": admission.admission_reason,
            "vital_signs": admission.vital_signs,
            "symptoms": admission.symptoms,
            "hospital_code": admission.hospital_code,
            "status": admission.status
        },
        "alerts": [
            {
                "alert_id": al.alert_id,
                "level": al.level,
                "message": al.message,
                "recommendations": al.recommendations,
                "agent_analysis": al.agent_analysis,
                "ai_report": al.ai_report,
                "hospital_notified": al.hospital_notified,
                "insurer_notified": al.insurer_notified,
                "created_at": al.created_at.isoformat() if al.created_at else None
            }
            for al in alerts
        ]
    }
