import uuid
from datetime import datetime
from .models import EmergencyAdmission, Alert, AlertLevel
from ..services.policy_service import PolicyService
from ..services.audit_service import AuditService


class EmergencyAlertAgent:
    def __init__(self):
        self.policy_service = PolicyService()
        self.audit_service = AuditService()

    def process_admission(self, admission: EmergencyAdmission) -> Alert:
        self.audit_service.log_action(
            admission.admission_id,
            "admission_received",
            {"patient_id": admission.patient_id, "policy_number": admission.policy_number}
        )

        policy = self.policy_service.get_policy(admission.policy_number)
        patient = self.policy_service.get_patient(admission.patient_id)

        alert_level = AlertLevel.INFO
        message = "Admission processed successfully"
        recommendations = []
        analysis_parts = []

        if not policy:
            alert_level = AlertLevel.CRITICAL
            message = "Policy not found"
            recommendations.append("Verify policy number")
            analysis_parts.append("Policy not found in system")
        else:
            validation = self.policy_service.validate_policy(policy)
            if not validation["valid"]:
                alert_level = AlertLevel.CRITICAL
                message = f"Policy issue: {validation['reason']}"
                recommendations.append("Contact insurance provider")
                analysis_parts.append(f"Policy validation failed: {validation['reason']}")
            else:
                analysis_parts.append("Policy is active and valid")

                if patient:
                    pre_ex_result = self.policy_service.check_pre_existences(patient, admission.admission_reason)
                    if pre_ex_result["has_relevant_pre_existences"]:
                        alert_level = AlertLevel.WARNING
                        message = "Patient has relevant pre-existing conditions"
                        recommendations.append("Review pre-existing conditions before treatment")
                        analysis_parts.append("Patient has relevant pre-existing conditions")

        if alert_level == AlertLevel.INFO:
            recommendations.append("Proceed with standard admission process")

        alert = Alert(
            alert_id=str(uuid.uuid4()),
            admission_id=admission.admission_id,
            level=alert_level,
            message=message,
            recommendations=recommendations,
            agent_analysis=" | ".join(analysis_parts),
            created_at=datetime.now()
        )

        self.audit_service.log_action(
            admission.admission_id,
            "agent_analysis_completed",
            {"alert_level": alert_level.value, "alert_id": alert.alert_id}
        )

        return alert
