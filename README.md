# PulseGuard
## Emergency Admission Alert System

Sistema agéntico de alerta temprana para ingresos a emergencias que utiliza IA para analizar y notificar automáticamente sobre admisiones de emergencia.

## Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Webhook       │     │   AI Agent      │     │  Notifications  │
│   (FastAPI)     │────▶│   (LangChain)   │────▶│   (Webhooks)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Admission     │     │   Policy &      │     │   Hospital &    │
│   Data          │     │   Patient DB    │     │   Insurer       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Flujo del Sistema

1. **Webhook Recibe Ingreso**: El sistema recibe datos de un ingreso a emergencias
2. **Agente IA Analiza**: Valida póliza, verifica preexistencias, analiza riesgo
3. **Genera Alertas**: Determina nivel de alerta (info/warning/critical)
4. **Notifica**: Envía alertas a admisiones del hospital y gestor de casos
5. **Auditoría**: Registra toda la actividad del agente

## Stack Tecnológico

- **Backend**: FastAPI (Python)
- **Agente IA**: LangChain + OpenAI GPT-4
- **Base de datos**: SQLite + JSON
- **Dashboard**: Streamlit
- **Notificaciones**: Webhooks HTTP

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/josecmirandac15/PulseGuard.git
cd PulseGuard

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tu API key de OpenAI
```

## Configuración

1. **API Key de OpenAI**:
   - Obtén tu API key en https://platform.openai.com/api-keys
   - Agrega la key en el archivo `.env`

2. **Webhooks**:
   - Configura las URLs de los webhooks en `.env`
   - Para demo, puedes usar los endpoints mock incluidos

## Ejecución

```bash
# Terminal 1: Iniciar API
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Iniciar Dashboard
streamlit run src/dashboard/app.py
```

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/webhook/admission` | Recibe ingreso de emergencia |
| GET | `/audit/{admission_id}` | Obtiene logs de auditoría |
| GET | `/audit` | Obtiene todos los logs |
| GET | `/health` | Health check |

## Casos de Prueba

1. **Póliza Activa**: `POL-2024-001` → Validación exitosa
2. **Póliza Vencida**: `POL-2024-002` → Alerta de póliza vencida
3. **Póliza Suspendida**: `POL-2024-004` → Alerta crítica
4. **Preexistencias**: `PAT-003` con enfermedades cardíacas → Revisión requerida
5. **Paciente sin preexistencias**: `PAT-004` → Proceso normal

## Dashboard

El dashboard Streamlit permite:
- Registrar nuevos ingresos de emergencia
- Visualizar logs de auditoría
- Monitorear estado del sistema

## Estructura del Proyecto

```
PulseGuard/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py          # Agente LangChain
│   │   └── models.py         # Modelos de datos
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py           # FastAPI application
│   ├── services/
│   │   ├── __init__.py
│   │   ├── policy_service.py
│   │   ├── notification_service.py
│   │   └── audit_service.py
│   └── dashboard/
│       └── app.py            # Streamlit dashboard
├── data/
│   ├── policies.json
│   ├── patients.json
│   └── audit_logs.json
├── tests/
│   └── test_services.py
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

## Licencia

MIT License
