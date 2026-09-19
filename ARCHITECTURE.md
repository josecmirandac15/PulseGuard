# PulseGuard v2.0 - Architecture & Development Plan
## hackIAthon Panamá 2026 - Reto 4

---

## 1. VISION DEL PROYECTO

**PulseGuard** es un sistema de alerta temprana que detecta ingresos a emergencia, valida pólizas de seguro, analiza preexistencias con IA y notifica simultáneamente al hospital y a la aseguradora en menos de 3 segundos.

### Diferenciadores para Ganar
1. **IA Explicable** - No solo dice "alerta", explica POR QUÉ con lógica clínica
2. **Tiempo Real** - Webhook → Análisis → Notificación en <3s
3. **Dashboard Ejecutivo** - Métricas en vivo que impresionan a los jueces
4. **Auditoría Completa** - Cada decisión trazable para compliance

---

## 2. STACK TECNOLÓGICO

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| **API** | FastAPI | Async, auto-docs, rápido |
| **DB** | PostgreSQL + SQLAlchemy | Relacional, ACID, zero hallucinations |
| **Migraciones** | Alembic | Versionado de schema |
| **IA** | OpenRouter API | Modelos gratuitos, sin vendor lock |
| **Cache** | Redis (opcional) | Para rate limiting y sesiones |
| **Dashboard** | Streamlit | Rápido de desarrollar, visual |
| **Container** | Docker + Docker Compose | Local reproducible |
| **Monitor** | Prometheus + Grafana (opcional) | Métricas para demo |

---

## 3. ARQUITECTURA DE CARPETAS

```
PulseGuard/
├── docker-compose.yml          # Orquestación de servicios
├── Dockerfile                  # Build de la API
├── .env.example                # Variables de entorno (template)
├── .gitignore
├── README.md
├── requirements.txt
├── alembic.ini                 # Config de migraciones
│
├── alembic/                    # Migraciones de DB
│   ├── versions/
│   └── env.py
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/                    # FastAPI Application
│   │   ├── __init__.py
│   │   ├── main.py             # App factory + lifespan
│   │   ├── deps.py             # Dependency injection
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── admissions.py   # POST /webhook/admission
│   │   │   ├── policies.py     # CRUD pólizas
│   │   │   ├── patients.py     # CRUD pacientes
│   │   │   ├── alerts.py       # GET alertas
│   │   │   └── dashboard.py    # Stats para dashboard
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── admission.py    # Pydantic models request/response
│   │       ├── policy.py
│   │       ├── patient.py
│   │       └── alert.py
│   │
│   ├── models/                 # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── base.py             # Base declarativa
│   │   ├── policy.py
│   │   ├── patient.py
│   │   ├── admission.py
│   │   ├── alert.py
│   │   └── audit_log.py
│   │
│   ├── services/               # Business Logic
│   │   ├── __init__.py
│   │   ├── policy_service.py   # Validación de pólizas
│   │   ├── patient_service.py  # Info de pacientes
│   │   ├── alert_service.py    # Generación de alertas
│   │   ├── notification_service.py  # Webhooks HTTP
│   │   ├── audit_service.py    # Logging de auditoría
│   │   └── ai_service.py       # OpenRouter integration
│   │
│   ├── agent/                  # Smart Agent Logic
│   │   ├── __init__.py
│   │   ├── engine.py           # Motor de reglas
│   │   ├── rules/              # Reglas clínicas
│   │   │   ├── __init__.py
│   │   │   ├── policy_rules.py
│   │   │   ├── preexistence_rules.py
│   │   │   └── risk_rules.py
│   │   └── prompts/            # Prompts para IA
│   │       ├── report_prompt.py
│   │       └── analysis_prompt.py
│   │
│   ├── receivers/              # Mock Services (para demo)
│   │   ├── __init__.py
│   │   ├── hospital_receiver.py
│   │   └── insurer_receiver.py
│   │
│   └── dashboard/              # Streamlit Dashboard
│       ├── app.py              # Entry point
│       ├── pages/
│       │   ├── 1_realtime.py   # Vista en tiempo real
│       │   ├── 2_history.py    # Historial de alertas
│       │   ├── 3_analytics.py  # Métricas y gráficas
│       │   └── 4_config.py     # Configuración
│       ├── components/
│       │   ├── charts.py       # Gráficas reutilizables
│       │   └── metrics.py      # KPIs cards
│       └── utils/
│           └── api_client.py   # Cliente para backend
│
├── data/
│   ├── seed.sql                # Datos iniciales para DB
│   └── policies.json           # Backup de datos
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures de pytest
│   ├── test_api/
│   ├── test_services/
│   └── test_agent/
│
├── scripts/
│   ├── seed_db.py              # Poblar DB con datos demo
│   └── test_webhook.py         # Script de prueba rápida
│
└── docs/
    ├── architecture.md
    └── api.md
```

---

## 4. ESQUEMA DE BASE DE DATOS

### Tablas Principales

```sql
-- Pacientes
CREATE TABLE patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    blood_type VARCHAR(5),
    allergies JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Preexistencias (tabla separada para queries eficientes)
CREATE TABLE pre_existences (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(patient_id),
    condition_name VARCHAR(100) NOT NULL,
    diagnosed_date DATE,
    severity VARCHAR(20),  -- mild, moderate, severe
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pólizas
CREATE TABLE policies (
    policy_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(patient_id),
    policy_number VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,  -- active, expired, suspended, cancelled
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    coverage_type VARCHAR(30),
    max_coverage_amount DECIMAL(12,2),
    provider VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ingresos de Emergencia
CREATE TABLE admissions (
    admission_id VARCHAR(30) PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(patient_id),
    policy_number VARCHAR(30) REFERENCES policies(policy_number),
    timestamp TIMESTAMP NOT NULL,
    admission_reason TEXT NOT NULL,
    vital_signs JSONB,
    symptoms JSONB DEFAULT '[]',
    hospital_code VARCHAR(20),
    status VARCHAR(20) DEFAULT 'received',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alertas Generadas
CREATE TABLE alerts (
    alert_id VARCHAR(36) PRIMARY KEY,
    admission_id VARCHAR(30) REFERENCES admissions(admission_id),
    level VARCHAR(20) NOT NULL,  -- info, warning, critical
    message TEXT NOT NULL,
    recommendations JSONB DEFAULT '[]',
    agent_analysis TEXT,
    ai_report TEXT,              -- Reporte generado por IA
    hospital_notified BOOLEAN DEFAULT FALSE,
    insurer_notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Log de Auditoría
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    admission_id VARCHAR(30),
    action VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_admissions_patient ON admissions(patient_id);
CREATE INDEX idx_admissions_timestamp ON admissions(timestamp);
CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_created ON alerts(created_at);
CREATE INDEX idx_policies_status ON policies(status);
```

---

## 5. ENDPOINTS API

### Core Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/webhook/admission` | Recibe ingreso (principal) |
| `GET` | `/health` | Health check |

### CRUD Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/patients` | Listar pacientes |
| `GET` | `/api/v1/patients/{id}` | Detalle paciente |
| `GET` | `/api/v1/policies` | Listar pólizas |
| `GET` | `/api/v1/policies/{number}` | Buscar por número |
| `GET` | `/api/v1/admissions` | Historial ingresos |
| `GET` | `/api/v1/alerts` | Listar alertas |
| `GET` | `/api/v1/alerts/stats` | Estadísticas |

### Dashboard Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/dashboard/realtime` | Stats en tiempo real |
| `GET` | `/api/v1/dashboard/hourly` | Ingresos por hora |
| `GET` | `/api/v1/dashboard/alerts-summary` | Resumen alertas |

---

## 6. FLUJO PRINCIPAL (Webhook → IA → Notificación)

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO PRINCIPAL                          │
└─────────────────────────────────────────────────────────────────┘

1. POST /webhook/admission
   │
   ▼
2. Validar Schema (Pydantic)
   │
   ▼
3. Buscar Póliza en PostgreSQL
   │
   ├─→ No existe → Alert CRITICAL "Póliza no encontrada"
   │
   └─→ Existe → Validar estado y fechas
                  │
                  ├─→ Vencida/Suspendida → Alert CRITICAL
                  │
                  └─→ Activa → Buscar preexistencias del paciente
                                │
                                ├─→ Tiene preexistencias relevantes → Alert WARNING
                                │
                                └─→ Sin preexistencias → Alert INFO
   
4. Generar Reporte con IA (OpenRouter)
   │
   ▼
5. Guardar Alerta en PostgreSQL
   │
   ▼
6. Notificar Webhooks (Hospital + Aseguradora)
   │
   ▼
7. Registrar en Audit Log
   │
   ▼
8. Retornar Respuesta
```

---

## 7. INTEGRACIÓN CON OPENROUTER API

### Configuración

```python
# src/services/ai_service.py
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Modelo gratuito recomendado
MODEL = "meta-llama/llama-3.1-8b-instruct:free"  # Gratis
# Alternativa: "google/gemma-2-9b-it:free"
```

### Prompt para Reporte Ejecutivo

```python
REPORT_PROMPT = """
Eres un sistema de alerta médica. Genera un reporte ejecutivo conciso.

DATOS DEL INGRESO:
- Paciente: {patient_name}, {age} años, {gender}
- Póliza: {policy_number} ({policy_status})
- Motivo: {admission_reason}
- Síntomas: {symptoms}
- Preexistencias: {pre_existences}
- Nivel de Alerta: {alert_level}

INSTRUCCIONES:
1. Resume la situación en 2-3 oraciones
2. Identifica riesgos clave
3. Recomienda acciones inmediatas
4. Sé conciso y profesional

FORMATO:
RESUMEN: [resumen]
RIESGOS: [lista]
ACCIONES: [lista]
"""
```

---

## 8. DOCKER COMPOSE

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://pulseguard:secret@db:5432/pulseguard
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - db
    volumes:
      - ./src:/app/src

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=pulseguard
      - POSTGRES_USER=pulseguard
      - POSTGRES_PASSWORD=secret
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/seed.sql:/docker-entrypoint-initdb.d/seed.sql

  hospital-receiver:
    image: hospital-receiver
    build:
      context: .
      dockerfile: Dockerfile.receiver
    ports:
      - "8001:8001"
    environment:
      - RECEIVER_TYPE=hospital

  insurer-receiver:
    image: insurer-receiver
    build:
      context: .
      dockerfile: Dockerfile.receiver
    ports:
      - "8002:8002"
    environment:
      - RECEIVER_TYPE=insurer

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000

volumes:
  postgres_data:
```

---

## 9. MODELOS DE DATOS (Pydantic)

```python
# src/api/schemas/admission.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EmergencyAdmission(BaseModel):
    admission_id: str = Field(..., example="ADM-20260918-001")
    patient_id: str = Field(..., example="PAT-001")
    policy_number: str = Field(..., example="POL-2024-001")
    timestamp: datetime
    admission_reason: str = Field(..., example="Dolor torácico agudo")
    vital_signs: Optional[dict] = Field(None, example={
        "heart_rate": 95,
        "blood_pressure": "140/90",
        "oxygen_saturation": 94
    })
    symptoms: List[str] = Field(..., example=["dolor pecho", "disnea"])
    hospital_code: str = Field(..., example="HOSP-001")

class AdmissionResponse(BaseModel):
    admission_id: str
    status: str
    alert_level: str
    message: str
    ai_report: Optional[str] = None
    hospital_notified: bool
    insurer_notified: bool
    processing_time_ms: float
```

---

## 10. DASHBOARD - PANTALLAS IMPACTANTES

### Pantalla 1: Vista en Tiempo Real (La estrella)
- **Mapa de calor** de ingresos por hora
- **Contador en vivo** de ingresos hoy
- **Últimas alertas** con scroll automático
- **Indicadores**: Tiempo promedio de respuesta

### Pantalla 2: Análisis de Alertas
- **Gráfica de pastel**: Distribución por nivel (INFO/WARNING/CRITICAL)
- **Timeline**: Evolución de alertas en 24h
- **Top 5**: Razones más comunes de alerta

### Pantalla 3: Métricas Ejecutivas
- **KPI Cards**: 
  - Total ingresos hoy
  - % con póliza válida
  - Tiempo promedio de notificación
  - Pacientes con preexistencias
- **Tabla de alertas** con filtros

### Pantalla 4: Configuración
- Webhook URLs
- Test de conectividad
- Simulador de ingresos

---

## 11. PLAN DE DESARROLLO (Fases)

### Fase 1: Fundamentos (Día 1-2)
- [ ] Configurar Docker Compose con PostgreSQL
- [ ] Crear modelos SQLAlchemy
- [ ] Configurar Alembic para migraciones
- [ ] Seed data en SQL
- [ ] Health check endpoint

### Fase 2: Core Logic (Día 3-4)
- [ ] Policy service con validación completa
- [ ] Patient service con preexistencias
- [ ] Alert service con niveles
- [ ] Agent engine con reglas clínicas

### Fase 3: API Completa (Día 5-6)
- [ ] POST /webhook/admission (endpoint principal)
- [ ] CRUD endpoints para queries
- [ ] Dashboard stats endpoints
- [ ] Error handling completo

### Fase 4: Integración IA (Día 7)
- [ ] OpenRouter client
- [ ] Prompt engineering para reportes
- [ ] Generación de reportes ejecutivos
- [ ] Cache de respuestas IA

### Fase 5: Receivers y Notificaciones (Día 8)
- [ ] Hospital receiver mock
- [ ] Insurer receiver mock
- [ ] Notification service con retry
- [ ] Audit logging completo

### Fase 6: Dashboard (Día 9-10)
- [ ] Layout principal
- [ ] Pantalla tiempo real
- [ ] Métricas y gráficas
- [ ] Simulador de pruebas

### Fase 7: Polish y Demo (Día 11-12)
- [ ] Tests end-to-end
- [ ] Performance testing
- [ ] Demo script
- [ ] Presentación para jueces

---

## 12. VARIABLES DE ENTORNO

```bash
# .env.example
# Database
DATABASE_URL=postgresql://pulseguard:secret@localhost:5432/pulseguard

# OpenRouter AI
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Webhooks
HOSPITAL_WEBHOOK_URL=http://localhost:8001/webhook/hospital
INSURER_WEBHOOK_URL=http://localhost:8002/webhook/insurer

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

---

## 13. COMANDOS DE DESARROLLO

```bash
# Iniciar todo
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ejecutar migraciones
docker-compose exec api alembic upgrade head

# Poblar datos demo
docker-compose exec api python scripts/seed_db.py

# Test rápido
curl -X POST http://localhost:8000/webhook/admission \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# Dashboard
streamlit run src/dashboard/app.py
```

---

## 14. MÉTRICAS PARA GANAR EL HACKATHON

Los jueces valoran:
1. **Funcionalidad** (40%) - Que el webhook funcione end-to-end
2. **Innovación** (25%) - Uso de IA explicable
3. **Presentación** (20%) - Dashboard visual + demo fluida
4. **Código** (15%) - Limpio, documentado, escalable

---

## 15. RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|------------|
| OpenRouter rate limit | Cache de respuestas, fallback a reglas |
| PostgreSQL caída | Health checks, reconnect logic |
| Demo falla en vivo | Scripts de backup, datos pre-cargados |
| Tiempo insuficiente | Priorizar Fase 1-5, dashboard simplificado |

---

**Documento preparado para: hackIAthon Panamá 2026**
**Equipo: PulseGuard**
**Fecha: Septiembre 2026**
