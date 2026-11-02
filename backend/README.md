# SQL Genius AI backend (optional service)

The maintained public playground remains a zero-cost static export. It does not call this backend or require accounts, credentials, hosted databases, Redis, or provider APIs. The Python implementation is retained and verified offline; that is not evidence of a production deployment.

## Install and verify

From the repository root, use **Python 3.11**:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r backend/requirements.txt
./scripts/check-backend.sh
```

That single check command prints versions, runs `pip check`, Ruff over the whole backend, meaningful whole-package mypy (including function bodies), and the complete offline pytest suite. It propagates every failure. CI calls the same script's named stages so failures are visible individually. No runtime stub installation or ignored checker exit status is used.

`requirements.in` declares backend application, retained integration, CI-tool and type-stub requirements. **`requirements.txt` is the authoritative fully pinned, hashed transitive resolution** consumed by normal installs and all backend container builds. The root `requirements.txt` belongs to the separate Streamlit example and is not the backend environment. Update an intended input pin, then deliberately refresh using the already locked pip-tools:

```bash
python -m piptools compile --resolver=backtracking --generate-hashes --allow-unsafe --upgrade \
  --output-file=backend/requirements.txt backend/requirements.in
./scripts/check-backend.sh
```

Review the generated resolution and prove a fresh installation before committing. Normal CI consumes it without resolving new versions. Unused LangChain was removed from backend inputs: no backend code imports it, and its old packaging constraints conflicted with maintained lock tooling. Required integration SDKs and stubs are retained; Redis uses its bundled types. Mypy import-only exceptions are limited to documented untyped Celery/Kombu, scikit-learn, and sqlparse libraries; backend code still receives type checking. Ruff's pinned default rule coverage and whole-backend scope are preserved.

## Offline tests and account contracts

Tests sanitize inherited service configuration before app imports, use a fresh in-memory SQLite database per test, reject INET/DNS calls, and capture email through an explicit double. Provider tests exercise the pinned SDK adapter with message doubles. Backup tests compress/archive real temporary fixture bytes with cloud/process boundaries doubled. No Render, paid model, SMTP, payment, or hosted production database is used. SQLite tests do not establish PostgreSQL-specific behavior.

Canonical `backend.*` imports and package markers prevent duplicate ORM registration. Native SQLAlchemy typing preserves the existing seven tables and 178-column schema. Passwords use direct bcrypt 5 hashing/verification, preserving existing standard bcrypt hashes. New password inputs over **72 UTF-8 bytes** receive 422 before persistence; login never truncates them. Incorrect/malformed hashes fail verification. Missing/invalid bearer credentials return **401** with a challenge; insufficient permissions remain **403**. Refresh returns its token-only response, and database/server errors return sanitized **500**, not an authentication error.

The authentication dependencies intentionally advance python-jose 3.3 to 3.5, which includes the fixes for [CVE-2024-33663/33664](https://github.com/mpdavis/python-jose/blob/master/CHANGELOG.md), and pin bcrypt 5.0.0 / cryptography 50.0.2. Direct bcrypt removes the observed Passlib backend-probe incompatibility without truncating passwords. The SDK/numerical changes repair observed API/type mismatches; this work is not a complete security certification of every legacy integration.

## Optional local service

After reviewing settings, run `uvicorn backend.main:app --reload` from the repository root. Startup creates tables in its configured account database: use only an authorized local/test database, and configure deployment JWT/encryption secrets explicitly. Optional provider generation needs server-only `ANTHROPIC_API_KEY`; never expose a `NEXT_PUBLIC_` key. The pinned Anthropic 0.8.1 adapter uses `beta.messages`, and missing credentials return 503 without a fallback. Redis/Celery are not prerequisites for the generation route; unconfigured cache returns misses.

The generation endpoint returns provenance and `not_checked`/`not_run` states; it never executes remote SQL. Compatibility execution stays disabled and fabricated metrics stay retired. The per-process limiter and permissive example deployment middleware are not production authorization or distributed abuse-protection guarantees.

## CI and containers

`Backend CI / test` uses Ubuntu 24.04 and Python 3.11. Official [checkout v5](https://github.com/actions/checkout/tree/v5) and [setup-python v6](https://github.com/actions/setup-python/tree/v6) use a Node 24 **action runtime**; that does not change the frontend's Node 22 build requirement. Pip caching is keyed to the lock; cold installation is validated independently.

Container files consume the same hash lock. In managed proxy environments, supply an optional BuildKit `proxy_ca` secret containing the trusted CA bundle for pip; it is mounted only during installation and never copied into an image. Container builds/runtime checks do not authorize deployment of this optional service.
