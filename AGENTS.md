# PulseGuard - Agent Instructions

## Architecture

Multi-service emergency admission alert system. 5 Docker containers orchestrated via `docker-compose.yml`:

| Service | Port | Container | Purpose |
|---------|------|-----------|---------|
| PostgreSQL | 5432 | pulseguard-db | Persistent data store |
| API | 8000 | pulseguard-api | Webhook + agent logic + AI reports |
| Hospital Receiver | 8001 | pulseguard-hospital | Mock hospital notifications |
| Insurer Receiver | 8002 | pulseguard-insurer | Mock insurer notifications |
| Dashboard | 8501 | pulseguard-dashboard | Streamlit UI |

## Run Commands

```bash
# Start all services
docker compose up -d

# Rebuild after code changes
docker compose up -d --build

# Rebuild specific service
docker compose up -d --build api

# Force recreate (picks up env var changes)
$env:OPENROUTER_API_KEY = "your-key"
docker compose up -d --force-recreate api

# View logs
docker compose logs api
docker compose logs hospital-receiver
```

**IMPORTANT**: Always use `docker compose` not bare `docker-compose`. On Windows, run from PowerShell at `D:\Proyectos\PulseGuard`.

## Data Flow

```
Dashboard → POST /api/v1/webhook/admission → API (8000)
    → policy_service.validate_policy() → patient_service.check_pre_existences()
    → alert_service.create_alert() → ai_service.generate_report()
    → notification_service.notify_hospital() (8001)
    → notification_service.notify_insurer() (8002)
    → Audit log written to PostgreSQL
```

## Key Files

```
src/
├── api/
│   ├── main.py                    # FastAPI app, lifespan, CORS, router includes
│   ├── routes/admissions.py       # POST /webhook/admission, GET /admissions
│   ├── routes/alerts.py           # GET /alerts, GET /alerts/stats
│   └── schemas/admission.py       # Pydantic request/response models
├── agent/engine.py                # Agent orchestrator - coordinates all services
├── models/                        # SQLAlchemy models (Patient, Policy, Admission, Alert, AuditLog)
│   └── base.py                    # Engine, SessionLocal, get_db dependency
├── services/
│   ├── policy_service.py          # Policy validation (active/expired/cancelled/suspended)
│   ├── patient_service.py         # Pre-existence matching by medical keywords
│   ├── alert_service.py           # Alert CRUD, levels: info/warning/critical
│   ├── notification_service.py    # HTTP POST to hospital + insurer receivers
│   └── ai_service.py              # OpenRouter API for AI reports, fallback to local
├── dashboard/app.py               # Streamlit UI (connects via API_URL env var)
└── receivers/
    ├── hospital_receiver.py       # Standalone FastAPI mock
    └── insurer_receiver.py        # Standalone FastAPI mock
```

## Environment Variables

Set in `.env` or docker-compose.yml:

- `OPENROUTER_API_KEY` - Required for AI reports (free tier works)
- `OPENROUTER_MODEL` - Currently `qwen/qwen3.8-27b:free`
- `DATABASE_URL` - PostgreSQL connection string
- `API_URL` - Dashboard uses this to find API (set to `http://api:8000` in Docker)

## Database

PostgreSQL 16 with schema + seed data in `data/seed.sql`. Tables: `patients`, `policies`, `pre_existences`, `admissions`, `alerts`, `audit_logs`.

Alembic configured but not yet used (schema loaded via seed.sql on first `docker compose up`).

To reset database: `docker compose down -v && docker compose up -d`

## Testing

```bash
# Smoke test - active policy + pre-existences (WARNING)
$body = @{admission_id="TEST-001";patient_id="PAT-001";policy_number="POL-2024-001";timestamp="2026-09-19T23:00:00";admission_reason="Chest pain";symptoms=@("chest pain");hospital_code="HOSP-001"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/webhook/admission" -Method POST -Body $body -ContentType "application/json"

# Verify health
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

## Gotchas

- **Docker env vars**: `${VAR:-}` in docker-compose.yml only picks up host env vars. Set them before `docker compose up` or use `--force-recreate`.
- **Volume mount**: `./src:/app/src` means code changes apply without rebuild, but env var changes need container restart.
- **Dashboard URL**: Must use `http://api:8000` (Docker service name), NOT `http://localhost:8000` when running inside container.
- **OpenRouter free tier**: 50 requests/day. Models with `:free` suffix cost nothing.
- **Receivers**: Standalone FastAPI apps, no `src.` imports. Built from `Dockerfile.receiver`.
- **Windows**: Always `python -m uvicorn` not bare `uvicorn`. Use PowerShell.
- **Database resets**: `docker compose down -v` removes the volume. Seed data re-runs on next `up`.
