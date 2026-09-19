import httpx
import os
from typing import Optional


class NotificationService:
    def __init__(self):
        self.hospital_webhook = os.getenv(
            "HOSPITAL_WEBHOOK_URL",
            "http://hospital-receiver:8001/webhook/hospital"
        )
        self.insurer_webhook = os.getenv(
            "INSURER_WEBHOOK_URL",
            "http://insurer-receiver:8002/webhook/insurer"
        )

    def notify_hospital(self, admission_data: dict, alert_data: dict) -> dict:
        payload = {
            "type": "admission_notification",
            "admission_id": admission_data.get("admission_id"),
            "patient_id": admission_data.get("patient_id"),
            "policy_number": admission_data.get("policy_number"),
            "hospital_code": admission_data.get("hospital_code"),
            "timestamp": admission_data.get("timestamp"),
            "admission_reason": admission_data.get("admission_reason"),
            "alert": alert_data
        }
        return self._send_webhook(self.hospital_webhook, payload)

    def notify_insurer(self, admission_data: dict, alert_data: dict) -> dict:
        payload = {
            "type": "insurer_notification",
            "admission_id": admission_data.get("admission_id"),
            "patient_id": admission_data.get("patient_id"),
            "policy_number": admission_data.get("policy_number"),
            "timestamp": admission_data.get("timestamp"),
            "admission_reason": admission_data.get("admission_reason"),
            "requires_case_manager_review": alert_data.get("level") in ["warning", "critical"],
            "alert": alert_data
        }
        return self._send_webhook(self.insurer_webhook, payload)

    def _send_webhook(self, url: str, payload: dict) -> dict:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(url, json=payload)
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
