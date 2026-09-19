import httpx
import os
from typing import Optional


class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3.8-27b:free")

    def generate_report(
        self,
        patient_data: dict,
        policy_data: dict,
        admission_data: dict,
        alert_level: str,
        analysis: str
    ) -> Optional[str]:
        if not self.api_key:
            return self._generate_fallback_report(
                patient_data, policy_data, admission_data, alert_level, analysis
            )

        prompt = self._build_prompt(
            patient_data, policy_data, admission_data, alert_level, analysis
        )

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Eres un sistema de alerta médica. Genera reportes ejecutivos concisos y profesionales en español."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 800
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return self._generate_fallback_report(
                        patient_data, policy_data, admission_data, alert_level, analysis
                    )
        except Exception:
            return self._generate_fallback_report(
                patient_data, policy_data, admission_data, alert_level, analysis
            )

    def _build_prompt(
        self,
        patient_data: dict,
        policy_data: dict,
        admission_data: dict,
        alert_level: str,
        analysis: str
    ) -> str:
        return f"""
DATOS DEL INGRESO:
- Paciente: {patient_data.get('name')}, {patient_data.get('age')} años, {patient_data.get('gender')}
- Tipo de Sangre: {patient_data.get('blood_type')}
- Póliza: {policy_data.get('policy_number')} ({policy_data.get('status')})
- Tipo Cobertura: {policy_data.get('coverage_type')}
- Monto Máximo: ${policy_data.get('max_coverage_amount')}
- Motivo: {admission_data.get('admission_reason')}
- Síntomas: {', '.join(admission_data.get('symptoms', []))}
- Nivel de Alerta: {alert_level}
- Análisis: {analysis}

INSTRUCCIONES:
1. Resume la situación en 2-3 oraciones
2. Identifica riesgos clave basado en preexistencias y síntomas
3. Recomienda acciones inmediatas
4. Sé conciso y profesional

FORMATO:
**RESUMEN:** [resumen]
**RIESGOS:** [lista]
**ACCIONES RECOMENDADAS:** [lista]
"""

    def _generate_fallback_report(
        self,
        patient_data: dict,
        policy_data: dict,
        admission_data: dict,
        alert_level: str,
        analysis: str
    ) -> str:
        report = f"**REPORTE DE INGRESO - {alert_level.upper()}**\n\n"
        report += f"**Paciente:** {patient_data.get('name')}, {patient_data.get('age')} años\n"
        report += f"**Póliza:** {policy_data.get('policy_number')} - {policy_data.get('status')}\n"
        report += f"**Motivo:** {admission_data.get('admission_reason')}\n\n"
        report += f"**ANÁLISIS:** {analysis}\n\n"

        if alert_level == "critical":
            report += "**ACCIÓN INMEDIATA:** Requiere intervención urgente del equipo médico.\n"
        elif alert_level == "warning":
            report += "**REVISIÓN:** Se requiere evaluación adicional antes del tratamiento.\n"
        else:
            report += "**ESTADO:** Ingreso procesado exitosamente.\n"

        return report
