# SQL Genius AI

**Natural-Language SQL and Analytics Playground**

SQL Genius AI demonstrates an inspectable analytics workflow: select and inspect a deterministic sample schema, express a question or choose a curated example, review/edit SQL, explicitly run an accepted read-only query in browser SQLite, and inspect/export the preview. An optional FastAPI integration can request schema-aware SQLite SQL from Anthropic; it never executes provider output automatically.

## Capability and evidence

| Capability | Status | Evidence path |
|---|---|---|
| Deterministic sample schemas and curated SQL | Implemented; exercised by local browser build | `sql-genius-frontend/src/data/` |
| Browser SQLite execution | Implemented with statement policy, engine preparation, and preview bounds | `src/lib/sql/database.ts`, `src/lib/sql/policy.ts` |
| Schema-aware generation request | Implemented; stubbed contract tests authored (not run here) | `backend/api/demo.py`, `backend/test_demo_contract.py` |
| Live Anthropic generation | Optional; requires server-only credentials; not called in repository checks | `backend/services/anthropic_service.py` |
| Account, cache, task, billing, and operations modules | Reference/optional code; not required by the public playground and not deployment evidence | `backend/services/`, `backend/tasks/` |
| Hosted deployments | Unverified in this cleanup | `DEPLOYMENT.md` |

## Flow and provenance

1. The selected fixture defines the exact tables, columns, types, and relationships.
2. Choosing a **Curated example** loads reviewed fixture SQL. Choosing **Generate** sends the schema structure, schema ID, dialect (`sqlite`), and question to `/api/v1/demo/sql-generate`.
3. Provider responses must be structured JSON with non-empty SQL, an explanation, and assumptions. Missing configuration and upstream/malformed responses are errors; there is no silent mock fallback.
4. Generation and Run are separate. At Run, the browser policy accepts one `SELECT` or read-only CTE and rejects mutation/schema/policy commands before SQLite preparation.
5. SQLite executes against synthetic fixture rows. Results are a preview capped at 500 rows and 1 MB. The UI attaches the source, dataset, execution state, and truncation state to the displayed SQL.

Passing the policy is not a correctness evaluation or a general security sandbox. sql.js runs client-side on the main thread; this cleanup does not claim hard CPU cancellation. Only bundled synthetic databases should be used. Uploaded/private database execution is not supported.

## No-key quick start

Requirements: Node.js 18+ and npm.

```bash
cd sql-genius-frontend
npm ci
npm run dev
```

Open `http://localhost:3000/demo`, choose **Sample Queries**, load a curated query, inspect it, then click **Execute**. Before development and production builds, a preparation script copies the matching WASM file from the locked `sql.js` package into the ignored `public/sql-wasm.wasm` runtime path. No binary is committed, and no CDN or API key is required for this path.

## Optional generation backend

Use Python 3.11 (the pinned backend dependencies predate newer Python releases):

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # review; do not commit it
export ANTHROPIC_API_KEY=...
uvicorn backend.main:app --reload
```

Set the frontend reverse proxy/environment according to its Next configuration. `ANTHROPIC_API_KEY` is server-only; never create a `NEXT_PUBLIC_` key. `ANTHROPIC_MODEL` is configurable and defaults to the model identifier retained for compatibility with the pinned SDK.

Mounted public routes are `/`, `/health`, and routes under `/api/v1` from `auth`, `users`, and `demo`. The generation contract is:

```json
POST /api/v1/demo/sql-generate
{"query":"List order identifiers","schema":{"id":"ecommerce","dialect":"sqlite","tables":[{"name":"orders","columns":[{"name":"order_id","type":"INTEGER"}]}],"relationships":[]}}
```

A successful response identifies `source`, actual `provider`/`model`, schema and dialect, provider timing/usage when available, `policy_status: "not_checked"`, and `execution_status: "not_run"`. `/api/v1/demo/execute-sandbox` is deprecated and returns `not_run`; remote arbitrary SQL execution is intentionally disabled. `/api/v1/demo/metrics` returns 410 because its values were fabricated.

## Checks

```bash
pytest -q backend/test_demo_contract.py
cd sql-genius-frontend && npm run lint && npm run build
```

These checks cover contracts and deterministic implementation behavior, not live-model text-to-SQL accuracy. See [`docs/PORTFOLIO_EVIDENCE.md`](docs/PORTFOLIO_EVIDENCE.md) for evidence categories, limitations, and external follow-up copy.

## Repository map

- `sql-genius-frontend/`: maintained Next.js playground and fixture data.
- `backend/api/demo.py`: optional public generation contract and disabled compatibility endpoints.
- `backend/services/anthropic_service.py`: optional provider adapter.
- `backend/test_demo_contract.py`: backend contract tests (provider calls are stubbed).
- `backend/services/`, `backend/tasks/`, `infrastructure/`: broader optional/reference modules; presence does not establish operation.
- `DEPLOYMENT.md`: maintained templates and rollout checks, not proof of deployment.

## Important limitations

No production benchmark, model-accuracy measurement, compliance certification, uptime result, adoption metric, or deployment verification is asserted. Generated SQL can be wrong. Review it, confirm business definitions, and use only the synthetic playground data. The in-memory backend rate limiter is per process and uses the directly observed peer address; it is not distributed abuse protection.
