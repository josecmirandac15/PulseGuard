# PulseGuard - Agent Instructions

## Architecture

Multi-service webhook system for emergency admission alerts. 4 FastAPI servers run independently:

| Service | Port | Entry Point | Purpose |
|---------|------|-------------|---------|
| API | 8000 | `src/api/main.py` | Webhook endpoint + audit |
| Hospital Receiver | 8001 | `src/receivers/hospital_receiver.py` | Mock hospital notifications |
| Insurer Receiver | 8002 | `src/receivers/insurer_receiver.py` | Mock insurer notifications |
| Dashboard | 8501 | `src/dashboard/app.py` | Streamlit UI |

## Run Commands

```bash
# Terminal 1 - API (must run first)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Hospital mock
python -m uvicorn src.receivers.hospital_receiver:app --host 0.0.0.0 --port 8001

# Terminal 3 - Insurer mock
python -m uvicorn src.receivers.insurer_receiver:app --host 0.0.0.0 --port 8002

# Terminal 4 - Dashboard
streamlit run src/dashboard/app.py --server.port 8501
```

## Data Flow

```
Dashboard → POST /webhook/admission → API (8000)
    → agent.process_admission() → policy validation + pre-existence check
    → POST to Hospital (8001)
    → POST to Insurer (8002)
    → Returns AdmissionResponse with notification status
```

## Key Files

- `src/agent/models.py` - All Pydantic models (EmergencyAdmission, Alert, Policy, Patient)
- `src/agent/agent.py` - Rule-based agent, no AI dependency
- `src/services/policy_service.py` - Reads `data/policies.json` and `data/patients.json` on init
- `src/services/notification_service.py` - Synchronous HTTP POST to receivers
- `src/services/audit_service.py` - Writes to `data/audit_logs.json`

## Testing

```bash
# Quick smoke test
python -c "import httpx; print(httpx.post('http://localhost:8000/webhook/admission', json={'admission_id':'T1','patient_id':'PAT-001','policy_number':'POL-2024-001','timestamp':'2026-09-18T16:00:00','admission_reason':'Chest pain','symptoms':['chest pain'],'hospital_code':'HOSP-001'}).json())"
```

## Gotchas

- `policy_service.py` loads JSON data at import time - restart API after data changes
- `audit_service.py` appends to `data/audit_logs.json` - file grows unbounded
- Receivers print to stdout only - no persistent storage
- No OpenAI/AI dependencies - agent is pure rule-based logic
- Windows: use `python -m uvicorn` not `uvicorn` directly
