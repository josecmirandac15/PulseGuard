from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from ..agent.models import EmergencyAdmission
from ..agent.agent import EmergencyAlertAgent
from ..services.notification_service import NotificationService
from ..services.audit_service import AuditService

load_dotenv()

app = FastAPI(
    title="PulseGuard API",
    description="Emergency Admission Alert System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = EmergencyAlertAgent()
notification_service = NotificationService(
    hospital_webhook=os.getenv("HOSPITAL_WEBHOOK_URL", "http://localhost:8001/webhook/hospital"),
    insurer_webhook=os.getenv("INSURER_WEBHOOK_URL", "http://localhost:8002/webhook/insurer")
)
audit_service = AuditService()


class AdmissionResponse(BaseModel):
    admission_id: str
    status: str
    alert_level: Optional[str] = None
    message: str


@app.get("/")
async def root():
    return {"message": "PulseGuard API - Emergency Alert System"}


@app.post("/webhook/admission", response_model=AdmissionResponse)
async def receive_admission(admission: EmergencyAdmission, background_tasks: BackgroundTasks):
    try:
        alert = await agent.process_admission(admission)

        background_tasks.add_task(
            notification_service.notify_hospital,
            admission,
            alert
        )
        background_tasks.add_task(
            notification_service.notify_insurer,
            admission,
            alert
        )

        return AdmissionResponse(
            admission_id=admission.admission_id,
            status="processed",
            alert_level=alert.level.value,
            message=alert.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/{admission_id}")
async def get_audit_logs(admission_id: str):
    logs = audit_service.get_logs_by_admission(admission_id)
    return {"admission_id": admission_id, "logs": logs}


@app.get("/audit")
async def get_all_audit_logs():
    logs = audit_service.get_all_logs()
    return {"total_logs": len(logs), "logs": logs}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PulseGuard"}
