# SQL Genius AI backend

FastAPI service containing the optional live-generation route plus account and reference integration modules. The browser sample playground does not require this service. Presence of tenant, cache, queue, billing, monitoring, or recovery code does not establish that those services are deployed or operational.

## Generation-only setup

Use Python 3.11 and install the pinned dependencies from the repository root:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
export ANTHROPIC_API_KEY=...       # optional; server-side only
export ANTHROPIC_MODEL=...         # optional configured identifier
uvicorn backend.main:app --reload
```

Application startup currently initializes its configured account database. Review `DATABASE_URL` and startup behavior before launching; do not point development commands at a database that is not authorized for testing. Account routes require their documented database/JWT configuration. Redis and Celery are not prerequisites for `/api/v1/demo/sql-generate`.

The generation route accepts the natural-language question plus a typed SQLite schema (ID, tables, columns, and relationships). It returns provider/model provenance, actual provider usage when available, and `not_checked`/`not_run` statuses. It does not validate or execute SQL. Missing credentials return 503; malformed or failed upstream responses return a sanitized 502. No fixture is silently substituted.

`POST /api/v1/demo/execute-sandbox` is a deprecated compatibility endpoint. Its object request shape is `{ "sql": "..." }`; it returns `execution_status: "not_run"` and no rows. `GET /api/v1/demo/metrics` returns 410.

The in-memory request limiter is best effort and per process. It uses the directly observed peer address rather than trusting forwarded headers. Configure explicit CORS origins and hosts for an authorized deployment.
