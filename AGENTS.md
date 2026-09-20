# PulseGuard — Agent Instructions

Reto 4, hackIAthon Panamá 2026: webhook de ingreso a emergencias → valida póliza y
pre-existencias (determinista) → notifica **simultáneamente** a admisiones del hospital
y al gestor de casos del seguro → panel en tiempo real.

## Branch & repo layout (read first)

- Work on **`deploy/web`**, not `main`. `main` is the old v1 (no Docker/Postgres/frontend).
  Push with `git push origin deploy/web`.
- This folder is its own git repo, nested inside the outer `hackiathon/` folder.
  The outer folder is a separate empty git repo holding only the hackathon PDFs — do not
  confuse the two or commit PDFs here.

## Architecture

- FastAPI (`src/api`), prefix **`/api/v1`**; health at `/health`, docs at `/docs`.
- SQLAlchemy + PostgreSQL (`src/models`); agent `src/agent/engine.py`; AI `src/services/ai_service.py`.
- Real-time hub: `src/core/realtime.py` (`ConnectionManager`) exposed at `WS /api/v1/ws/alerts`.
- Frontend: plain HTML/CSS/JS in `web/` (**no Streamlit**). Three portals: `/` (registro),
  `/hospital` (admisiones), `/aseguradora` (gestor de casos); share `web/common.js`.
- nginx serves `web/` and proxies `/api/` (with WebSocket upgrade) — `deploy/nginx/default.conf`.
- docker-compose services: `db`, `api`, `hospital-receiver`, `insurer-receiver`, `nginx`.
  Receivers are standalone FastAPI mocks (no `src.` imports), built from `Dockerfile.receiver`.

## Hard-won gotchas

- **Tests are broken on `deploy/web`.** `tests/test_services.py` targets the old v1
  `PolicyService()` (no DB session, `.policies`, `.check_pre_existences`). `pytest` fails;
  this is not a regression. Rewrite against the SQLAlchemy services before trusting it.
- **Decisions are deterministic, the LLM only writes prose.** Policy validity and
  pre-existence matching are SQL/Python. Without `OPENROUTER_API_KEY`, `ai_service` uses
  `_generate_fallback_report()`. Never move coverage logic into the AI.
- `policy_service.validate_policy()` returns Spanish lowercase reasons (`expirada`,
  `suspendida`, `cancelada`, `aún no vigente`); `engine.py` interpolates them into the
  Spanish message. Keep user-facing strings in Spanish and clinical.
- Alert levels: `info`=sin observaciones, `warning`=requiere revisión,
  `critical`=atención inmediata (administrative action — emergency care is never denied).
- `POST /api/v1/webhook/admission` is idempotent by `admission_id` (duplicates no longer 500).
  The agent runs in a threadpool; the WS broadcast happens after processing.
- **Windows:** use `python -m uvicorn`, not bare `uvicorn`. Receivers print emojis, so
  UTF-8 is forced (`sys.stdout.reconfigure` + `PYTHONUTF8=1`); removing it crashes on cp1252.
- **Static caching:** Cloudflare caches `.js`/`.css`. After editing frontend assets, bump the
  `?v=N` query in the HTML files; nginx sets `Cache-Control: no-store`.
- **File perms:** nginx (uid 101) must read `web/`. `deploy.sh` applies `umask 022` +
  `chmod -R a+rX web`; skip it and you get 403 on every static file.
- Schema comes from `data/seed.sql` (Postgres, first volume init) and
  `Base.metadata.create_all` at API startup. Alembic is configured but unused at runtime.
- `./src:/app/src` is bind-mounted into `api`: code changes apply without rebuild, but
  dependency/env changes need `docker compose up -d --build` or `--force-recreate`.

## Run, test, verify

```bash
cp .env.example .env
docker compose up -d --build          # stack at http://localhost:8080
docker compose up -d --build api      # rebuild one service
docker compose logs -f api
docker compose down -v && docker compose up -d   # reset DB (re-seeds)
```

- Smoke test: `POST /api/v1/webhook/admission` with JSON (see README). Active policy +
  pre-existing condition → `warning`; expired/suspended/unknown → `critical`.
- WS check: connect to `ws://localhost:8080/api/v1/ws/alerts`; expect `{"event":"connected"}`
  then `admission.processed` with `stats`.
- **No-Docker local run (Windows, no Postgres):** models use generic SQLAlchemy types, so
  `DATABASE_URL=sqlite:///./data/pulseguard_test.db` works with
  `python -m uvicorn src.api.main:app --port 8000`. `create_all` makes *empty* tables — seed
  patients/policies/pre_existences yourself from `data/patients.json` + `data/policies.json`
  (JSON field `condition` maps to model `condition_name`). `psycopg2` is not needed for SQLite.

## Deploy

- Public: https://pulseguard.sweetcode.studio (Cloudflare Tunnel → nginx).
- On the server (repo at `/opt/pulseguard`): run `./deploy.sh` — pulls `origin/deploy/web`,
  rebuilds, restarts nginx, fixes perms.
- `.env` is gitignored and lives only on the server; never commit it.
