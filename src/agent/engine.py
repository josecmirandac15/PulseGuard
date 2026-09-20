from datetime import datetime
from typing import Optional
import uuid

from src.models.base import SessionLocal
from src.models import Admission, Alert, AuditLog
from src.services.policy_service import PolicyService
from src.services.patient_service import PatientService
from src.services.alert_service import AlertService
from src.services.ai_service import AIService


class EmergencyAlertAgent:
    def __init__(self):
        self.ai_service = AIService()

    def process_admission(self, admission_data: dict) -> dict:
        db = SessionLocal()
        try:
            policy_service = PolicyService(db)
            patient_service = PatientService(db)
            alert_service = AlertService(db)

            admission_id = admission_data.get("admission_id")
            policy_number = admission_data.get("policy_number")
            patient_id = admission_data.get("patient_id")

            self._log_action(db, admission_id, "admission_received", {
                "patient_id": patient_id,
                "policy_number": policy_number
            })

            policy = policy_service.get_policy_by_number(policy_number)
            patient = patient_service.get_patient(patient_id)

            alert_level = "info"
            message = "Ingreso registrado. Cobertura vigente sin observaciones."
            recommendations = []
            analysis_parts = []

            if not policy:
                alert_level = "critical"
                message = "No se encontró la póliza del asegurado."
                recommendations.append("Verificar el número de póliza con la aseguradora")
                analysis_parts.append("Policy not found in system")
            else:
                validation = policy_service.validate_policy(policy)
                if not validation["valid"]:
                    alert_level = "critical"
                    message = f"Cobertura no vigente: póliza {validation['reason']}."
                    recommendations.append("Contactar al gestor de casos de la aseguradora")
                    analysis_parts.append(f"Policy validation failed: {validation['reason']}")
                else:
                    analysis_parts.append("Policy is active and valid")

                    if patient:
                        pre_ex_result = patient_service.check_pre_existences(
                            patient_id, admission_data.get("admission_reason", "")
                        )
                        if pre_ex_result["has_relevant"]:
                            alert_level = "warning"
                            message = "Cobertura vigente. El paciente presenta pre-existencias relevantes."
                            recommendations.append("Revisar las pre-existencias antes del tratamiento")
                            analysis_parts.append(
                                f"Relevant conditions: {', '.join([c['condition'] for c in pre_ex_result['relevant_conditions']])}"
                            )

            if alert_level == "info":
                recommendations.append("Continuar con el proceso de admisión estándar")

            analysis = " | ".join(analysis_parts)

            patient_data = {
                "name": patient.name if patient else "Unknown",
                "age": patient.age if patient else 0,
                "gender": patient.gender if patient else "Unknown",
                "blood_type": patient.blood_type if patient else "Unknown"
            }
            policy_data = {
                "policy_number": policy.policy_number if policy else policy_number,
                "status": policy.status if policy else "unknown",
                "coverage_type": policy.coverage_type if policy else "unknown",
                "max_coverage_amount": float(policy.max_coverage_amount) if policy and policy.max_coverage_amount else 0
            }

            ai_report = self.ai_service.generate_report(
                patient_data, policy_data, admission_data, alert_level, analysis
            )

            alert = alert_service.create_alert(
                admission_id=admission_id,
                level=alert_level,
                message=message,
                recommendations=recommendations,
                agent_analysis=analysis,
                ai_report=ai_report
            )

            self._log_action(db, admission_id, "agent_analysis_completed", {
                "alert_level": alert_level,
                "alert_id": alert.alert_id
            })

            from src.services.notification_service import NotificationService
            notification_service = NotificationService()
            hospital_result = notification_service.notify_hospital(admission_data, {
                "level": alert_level,
                "message": message,
                "recommendations": recommendations
            })
            insurer_result = notification_service.notify_insurer(admission_data, {
                "level": alert_level,
                "message": message,
                "agent_analysis": analysis,
                "recommendations": recommendations
            })

            alert_service.update_alert_notifications(
                alert.alert_id,
                hospital_notified=hospital_result.get("success", False),
                insurer_notified=insurer_result.get("success", False)
            )

            self._log_action(db, admission_id, "notifications_sent", {
                "hospital": hospital_result,
                "insurer": insurer_result
            })

            return {
                "admission_id": admission_id,
                "status": "processed",
                "alert_level": alert_level,
                "message": message,
                "recommendations": recommendations,
                "ai_report": ai_report,
                "patient_name": patient.name if patient else "Unknown",
                "policy_number": policy_number,
                "admission_reason": admission_data.get("admission_reason"),
                "hospital_code": admission_data.get("hospital_code"),
                "timestamp": admission_data.get("timestamp"),
                "hospital_notified": hospital_result.get("success", False),
                "insurer_notified": insurer_result.get("success", False)
            }

        finally:
            db.close()

    def _log_action(self, db, admission_id: str, action: str, details: dict):
        log = AuditLog(
            admission_id=admission_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
