# PulseGuard — Sistema de Alerta Temprana de Ingresos a Emergencias

Solución al **Reto 4** del *hackIAthon Panamá 2026*.

Un **webhook** se activa cuando un asegurado ingresa a la emergencia de un hospital.
Un agente revisa **instantáneamente** la validez de la póliza y el historial de
pre-existencias, y envía una **notificación simultánea** al departamento de
admisiones del hospital y al gestor de casos del seguro, con un panel en
**tiempo real**.

- **Demo en vivo:** https://pulseguard.sweetcode.studio
- **API Docs:** https://pulseguard.sweetcode.studio/docs

---

## Arquitectura

```
                    ┌──────────────────────────────┐
   Navegador  ──────►  nginx  (web estática + proxy)│
   (panel RT)  ◄─WS──┤   /            → web/        │
                    │   /api/v1/*    → api:8000    │
                    └──────────────┬───────────────┘
                                   │
                         ┌─────────▼──────────┐
   Webhook admisión ────►│  FastAPI (api)     │
                         │  /api/v1/webhook/  │
                         │  admission         │
                         └───────┬────────────┘
                                 │ EmergencyAlertAgent (determinista)
                     ┌───────────┼───────────────┐
                     ▼           ▼               ▼
             ┌────────────┐ ┌──────────┐  ┌──────────────┐
             │ PostgreSQL │ │ IA (LLM) │  │ WebSocket hub│
             │ pólizas +  │ │ síntesis │  │  /ws/alerts  │
             │ pre-exist. │ │ reporte  │  └──────┬───────┘
             └────────────┘ └──────────┘         │
                                                 ▼
                              ┌───────────────────────────────┐
                              │ hospital-receiver  (8001)     │
                              │ insurer-receiver   (8002)     │
                              └───────────────────────────────┘
```

## Stack

| Capa | Tecnología |
|------|------------|
| API / Webhook | FastAPI + Uvicorn |
| Base de datos | PostgreSQL 16 + SQLAlchemy + Alembic |
| IA | OpenRouter (modelo configurable) con *fallback* determinista |
| Tiempo real | WebSocket nativo (`/api/v1/ws/alerts`) |
| Frontend | HTML + CSS + JS (sin frameworks, sin dependencias externas) |
| Proxy / Deploy | nginx + Docker Compose + Cloudflare Tunnel |

> **Decisión de diseño:** la lógica crítica (vigencia de póliza y pre-existencias)
> es **determinista** (SQL/Python). La IA **solo redacta** el reporte; nunca decide
> el nivel de alerta.

---

## Flujo del agente

1. `POST /api/v1/webhook/admission` recibe el ingreso.
2. Se guarda la admisión en PostgreSQL.
3. `EmergencyAlertAgent`:
   - busca la póliza y la valida (activa / expirada / suspendida / cancelada / no existe),
   - busca al paciente y cruza sus **pre-existencias** con el motivo de ingreso,
   - determina el nivel: `info`, `warning` o `critical`,
   - pide a la IA un **reporte ejecutivo** (o usa el fallback),
   - **notifica simultáneamente** al hospital y a la aseguradora,
   - registra todo en `audit_logs`.
4. El resultado se **emite por WebSocket** a todos los paneles conectados.

### Niveles de alerta

| Nivel | Cuándo |
|-------|--------|
| `critical` | Póliza inexistente, expirada, suspendida o cancelada |
| `warning` | Póliza válida **con** pre-existencias relevantes |
| `info` | Póliza válida sin pre-existencias relevantes |

---

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/webhook/admission` | Recibe el ingreso y dispara el agente |
| `GET` | `/api/v1/admissions` | Listado de admisiones |
| `GET` | `/api/v1/admissions/{id}` | Detalle + alertas |
| `GET` | `/api/v1/alerts` | Alertas (filtro `?level=`) |
| `GET` | `/api/v1/alerts/stats` | KPIs |
| `GET` | `/api/v1/dashboard/stats` | KPIs del panel |
| `WS` | `/api/v1/ws/alerts` | Canal en tiempo real |
| `GET` | `/health` | Estado de la API y la base de datos |

Ejemplo:

```bash
curl -X POST https://pulseguard.sweetcode.studio/api/v1/webhook/admission \
  -H "Content-Type: application/json" \
  -d '{
    "admission_id": "ADM-001",
    "patient_id": "PAT-001",
    "policy_number": "POL-2024-001",
    "timestamp": "2026-09-20T05:00:00",
    "admission_reason": "Chest pain",
    "symptoms": ["chest pain", "dyspnea"],
    "hospital_code": "HOSP-001"
  }'
```

---

## Ejecución local

### Docker (recomendado)

```bash
cp .env.example .env        # ajusta POSTGRES_PASSWORD y OPENROUTER_API_KEY
docker compose up -d --build
```

Abre `http://localhost:8080`.

### Redespliegue en el servidor

```bash
./deploy.sh
```

Actualiza el código, reconstruye los contenedores y reinicia el proxy.

### Sin Docker

```bash
pip install -r requirements.txt
# requiere PostgreSQL accesible vía DATABASE_URL
uvicorn src.api.main:app --port 8000
```

---

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Cadena de conexión PostgreSQL |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciales de la BD (docker-compose) |
| `OPENROUTER_API_KEY` | Clave de OpenRouter (opcional: si falta, usa fallback) |
| `OPENROUTER_MODEL` | Modelo a usar (por defecto `qwen/qwen3.8-27b:free`) |
| `HOSPITAL_WEBHOOK_URL` | Endpoint del hospital |
| `INSURER_WEBHOOK_URL` | Endpoint de la aseguradora |
| `PULSEGUARD_BIND` | Interfaz de bind de nginx/API |
| `PULSEGUARD_HTTP_PORT` | Puerto público de nginx |

---

## Estructura

```
src/
  api/            FastAPI: rutas, esquemas
    routes/       admissions, alerts, dashboard, ws (WebSocket)
  core/           realtime.py (hub WebSocket)
  models/         SQLAlchemy (patients, policies, pre_existences, admissions, alerts, audit_logs)
  services/       policy, patient, alert, notification, ai
  agent/engine.py Orquestador determinista
  receivers/      Mocks hospital / aseguradora
web/              Frontend estático (panel en tiempo real)
deploy/nginx/     Reverse proxy
data/seed.sql     Esquema + datos de prueba
```

## Datos de prueba

`data/seed.sql` incluye 8 pacientes y 8 pólizas con todos los estados
(activas, expirada, suspendida, cancelada) y pre-existencias variadas.

---

## Entregables hackIAthon

- **Repositorio:** este repo (rama `main`).
- **Agente en ejecución:** https://pulseguard.sweetcode.studio
- **Herramientas de IA usadas:** [`docs/HERRAMIENTAS-IA.pdf`](docs/HERRAMIENTAS-IA.pdf) (fuente: [`docs/HERRAMIENTAS-IA.md`](docs/HERRAMIENTAS-IA.md)).
