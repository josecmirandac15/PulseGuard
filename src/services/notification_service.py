import httpx
from typing import Optional
from ..agent.models import EmergencyAdmission, Alert


class NotificationService:
    def __init__(self, hospital_webhook: str, insurer_webhook: str):
        self.hospital_webhook = hospital_webhook
        self.insurer_webhook = insurer_webhook

    async def notify_hospital(self, admission: EmergencyAdmission, alert: Optional[Alert] = None):
        payload = {
            "type": "admission_notification",
            "admission_id": admission.admission_id,
            "patient_id": admission.patient_id,
            "policy_number": admission.policy_number,
            "hospital_code": admission.hospital_code,
            "timestamp": admission.timestamp.isoformat(),
            "admission_reason": admission.admission_reason
        }

        if alert:
            payload["alert"] = {
                "level": alert.level.value,
                "message": alert.message,
                "recommendations": alert.recommendations
            }

        return await self._send_webhook(self.hospital_webhook, payload)

    async def notify_insurer(self, admission: EmergencyAdmission, alert: Optional[Alert] = None):
        payload = {
            "type": "insurer_notification",
            "admission_id": admission.admission_id,
            "patient_id": admission.patient_id,
            "policy_number": admission.policy_number,
            "timestamp": admission.timestamp.isoformat(),
            "admission_reason": admission.admission_reason,
            "requires_case_manager_review": alert.level.value in ["warning", "critical"] if alert else False
        }

        if alert:
            payload["alert"] = {
                "level": alert.level.value,
                "message": alert.message,
                "agent_analysis": alert.agent_analysis,
                "recommendations": alert.recommendations
            }

        return await self._send_webhook(self.insurer_webhook, payload)

    async def _send_webhook(self, url: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=10.0,
                    headers={"Content-Type": "application/json"}
                )
                return {
                    "success": response.status_code in [200, 201],
                    "status_code": response.status_code,
                    "response": response.text
                }
        except httpx.RequestError as e:
            return {
                "success": False,
                "error": str(e),
                "fallback": "logged_to_audit"
            }
