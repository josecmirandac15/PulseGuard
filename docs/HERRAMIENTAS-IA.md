# Herramientas de IA utilizadas — PulseGuard

Documento de sustento para el entregable *"PDF con el detalle de las herramientas
de IA utilizadas durante el desarrollo"* del hackIAthon Panamá 2026.

## 1. IA en el producto (runtime)

| Herramienta | Propósito | Aplicación | Resultados |
|-------------|-----------|------------|------------|
| **OpenRouter API** | Gateway de LLM para sintetizar el reporte médico-administrativo | `src/services/ai_service.py` — recibe el contexto ya resuelto (paciente, póliza, pre-existencias relevantes, nivel de alerta) y redacta un reporte ejecutivo en español (máx. 120 palabras) | Reporte estructurado por ingreso, con resumen, riesgo y acción recomendada |
| **Modelo LLM** (`OPENROUTER_MODEL`, por defecto `qwen/qwen3.8-27b:free`) | Generación de texto | Igual que el anterior | Reportes coherentes y consistentes |
| **Fallback determinista** | Garantizar disponibilidad sin API key o sin red | `_generate_fallback_report()` | El flujo nunca se rompe; siempre hay reporte |

**Principio de diseño:** la IA **no toma decisiones de cobertura**. La vigencia de
póliza y la detección de pre-existencias se resuelven de forma determinista
(PostgreSQL + Python). La IA solo **redacta**.

## 2. IA en el desarrollo (herramientas de apoyo)

| Herramienta | Propósito | Aplicación | Resultados |
|-------------|-----------|------------|------------|
| **opencode** (asistente de codificación) | Arquitectura, implementación y despliegue | Diseño de la arquitectura, endpoints FastAPI, hub WebSocket, frontend, Docker/nginx y automatización del despliegue | Reducción del tiempo de desarrollo; código consistente y documentado |
| **Modelo de lenguaje del asistente** | Generación/revisión de código y documentación | Redacción de componentes, revisión de errores de encoding, diseño de prompts | Iteraciones rápidas sobre backend, frontend y despliegue |

## 3. Prompt del reporte (resumen)

```
Eres un asistente médico-administrativo. NO decidas cobertura; el sistema ya
determinó: nivel=<LEVEL>, póliza=<STATUS>, pre-existencias relevantes=<LIST>.
Redacta un reporte ejecutivo de máximo 120 palabras con:
1) Resumen del ingreso  2) Riesgo detectado  3) Acción recomendada.
Tono profesional, español. No inventes datos que no estén en el contexto.
```
