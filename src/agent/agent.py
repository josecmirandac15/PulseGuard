import os
import uuid
import json
from datetime import datetime
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from .models import EmergencyAdmission, Alert, AlertLevel
from ..services.policy_service import PolicyService
from ..services.audit_service import AuditService


class EmergencyAlertAgent:
    def __init__(self):
        self.policy_service = PolicyService()
        self.audit_service = AuditService()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key and self.openai_api_key != "your_openai_api_key_here":
            self.llm = ChatOpenAI(
                model=os.getenv("AGENT_MODEL", "gpt-4"),
                temperature=0
            )
            self.tools = self._create_tools()
            self.agent = self._create_agent()
        else:
            self.llm = None
            self.tools = []
            self.agent = None
            print("Warning: OPENAI_API_KEY not configured. Using rule-based fallback.")

    def _create_tools(self) -> list:
        @tool
        def validate_policy(policy_number: str) -> str:
            """Validate insurance policy status. Input: policy_number"""
            policy = self.policy_service.get_policy(policy_number)
            if not policy:
                return f"Policy {policy_number} not found"
            validation = self.policy_service.validate_policy(policy)
            return f"Policy Status: {policy.status.value}, Valid: {validation['valid']}, Reason: {validation['reason']}"

        @tool
        def get_patient_info(patient_id: str) -> str:
            """Get patient information. Input: patient_id"""
            patient = self.policy_service.get_patient(patient_id)
            if not patient:
                return f"Patient {patient_id} not found"
            return f"Patient: {patient.name}, Age: {patient.age}, Gender: {patient.gender}, Pre-existences: {len(patient.pre_existences)}"

        @tool
        def check_pre_existences(patient_id: str, admission_reason: str) -> str:
            """Check patient pre-existences. Input: patient_id and admission_reason"""
            patient = self.policy_service.get_patient(patient_id)
            if not patient:
                return f"Patient {patient_id} not found"
            result = self.policy_service.check_pre_existences(patient, admission_reason)
            return f"Relevant pre-existences: {result['has_relevant_pre_existences']}, Requires review: {result['requires_review']}"

        return [validate_policy, get_patient_info, check_pre_existences]

    def _create_agent(self):
        system_prompt = """You are an AI agent for PulseGuard, an emergency admission alert system.

Your role is to analyze emergency admissions and:
1. Validate the insurance policy status
2. Check patient information and pre-existences
3. Determine the alert level based on the analysis
4. Provide recommendations

Always respond in JSON format with:
{
    "alert_level": "info|warning|critical",
    "message": "Brief description of the analysis",
    "recommendations": ["list", "of", "recommendations"],
    "agent_analysis": "Detailed analysis explanation"
}"""

        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt
        )

    async def process_admission(self, admission: EmergencyAdmission) -> Alert:
        self.audit_service.log_action(
            admission.admission_id,
            "admission_received",
            {"patient_id": admission.patient_id, "policy_number": admission.policy_number}
        )

        if not self.agent:
            return self._rule_based_analysis(admission)

        input_text = f"""Process this emergency admission:
        - Admission ID: {admission.admission_id}
        - Patient ID: {admission.patient_id}
        - Policy Number: {admission.policy_number}
        - Reason: {admission.admission_reason}
        - Timestamp: {admission.timestamp.isoformat()}
        
        Please validate the policy, check patient info, and determine alert level."""

        try:
            result = await self.agent.ainvoke({"messages": [{"role": "user", "content": input_text}]})

            messages = result.get("messages", [])
            output = ""

            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content:
                    output = msg.content
                    break

            if isinstance(output, str):
                try:
                    analysis = json.loads(output)
                except:
                    analysis = {
                        "alert_level": "info",
                        "message": output,
                        "recommendations": [],
                        "agent_analysis": output
                    }
            else:
                analysis = output

            alert_level = AlertLevel(analysis.get("alert_level", "info"))

            alert = Alert(
                alert_id=str(uuid.uuid4()),
                admission_id=admission.admission_id,
                level=alert_level,
                message=analysis.get("message", "Analysis completed"),
                recommendations=analysis.get("recommendations", []),
                agent_analysis=analysis.get("agent_analysis", ""),
                created_at=datetime.now()
            )

            self.audit_service.log_action(
                admission.admission_id,
                "agent_analysis_completed",
                {"alert_level": alert_level.value, "alert_id": alert.alert_id}
            )

            return alert

        except Exception as e:
            self.audit_service.log_action(
                admission.admission_id,
                "agent_error",
                {"error": str(e)}
            )

            return Alert(
                alert_id=str(uuid.uuid4()),
                admission_id=admission.admission_id,
                level=AlertLevel.CRITICAL,
                message=f"Error processing admission: {str(e)}",
                recommendations=["Manual review required"],
                agent_analysis=f"Agent error: {str(e)}",
                created_at=datetime.now()
            )

    def _rule_based_analysis(self, admission: EmergencyAdmission) -> Alert:
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
                        recommendations.append("Review pre-existing conditions")
                        analysis_parts.append("Patient has relevant pre-existing conditions that may affect treatment")
        
        if alert_level == AlertLevel.INFO:
            recommendations.append("Proceed with standard admission process")
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            admission_id=admission.admission_id,
            level=alert_level,
            message=message,
            recommendations=recommendations,
            agent_analysis=" | ".join(analysis_parts) if analysis_parts else "Rule-based analysis completed",
            created_at=datetime.now()
        )
        
        self.audit_service.log_action(
            admission.admission_id,
            "rule_based_analysis_completed",
            {"alert_level": alert_level.value, "alert_id": alert.alert_id}
        )
        
        return alert
