# SQL Genius AI

**Natural-Language SQL and Analytics Playground**

SQL Genius AI demonstrates an inspectable analytics workflow: select and inspect a deterministic sample schema, express a question or choose a curated example, review/edit SQL, explicitly run an accepted read-only query in browser SQLite, and inspect/export the preview. Generation now runs entirely in the browser with no account, API key, backend, or per-request cost.

## Capability and evidence

| Capability | Status | Evidence path |
|---|---|---|
| Deterministic sample schemas and curated SQL | Implemented; exercised by local browser build | `sql-genius-frontend/src/data/` |
| Browser SQLite execution | Implemented with statement policy, engine preparation, and preview bounds | `src/lib/sql/database.ts`, `src/lib/sql/policy.ts` |
| Zero-cost schema-aware generation | Implemented locally with reviewed-intent retrieval and a conservative schema fallback | `src/lib/sql/local-generator.ts`, `tests/local-generator.test.ts` |
| Legacy Anthropic backend route | Retained for compatibility; not used by the playground | `backend/api/demo.py`, `backend/services/anthropic_service.py` |
| Account, cache, task, billing, and operations modules | Reference/optional code; not required by the public playground and not deployment evidence | `backend/services/`, `backend/tasks/` |
| Hosted deployments | Unverified in this cleanup | `DEPLOYMENT.md` |

## Flow and provenance

1. The selected fixture defines the exact tables, columns, types, and relationships.
2. Choosing a **Curated example** loads reviewed fixture SQL. Choosing **Generate** matches the question against the selected schema's reviewed query library in the browser. Novel requests receive a conservative table preview or row-count query rather than invented joins or business logic.
3. The UI explains whether it selected a reviewed intent or used the conservative fallback, shows match confidence and assumptions, and makes no network generation request.
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

## Legacy optional generation backend

The public playground does not need this service. The route remains available for compatibility or private deployments that intentionally want provider-backed generation.

Use Python 3.11 (the pinned backend dependencies predate newer Python releases):

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env  # review; do not commit it
export ANTHROPIC_API_KEY=...
uvicorn backend.main:app --reload
```

`ANTHROPIC_API_KEY` is server-only; never create a `NEXT_PUBLIC_` key. `ANTHROPIC_MODEL` is configurable and defaults to the model identifier retained for compatibility with the pinned SDK.

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

These checks cover contracts and deterministic implementation behavior. The local generator intentionally favors predictable, reviewed SQL over pretending to understand ambiguous business questions. See [`docs/PORTFOLIO_EVIDENCE.md`](docs/PORTFOLIO_EVIDENCE.md) for evidence categories, limitations, and external follow-up copy.

## Repository map

- `sql-genius-frontend/`: maintained Next.js playground and fixture data.
- `backend/api/demo.py`: optional public generation contract and disabled compatibility endpoints.
- `backend/services/anthropic_service.py`: optional provider adapter.
- `backend/test_demo_contract.py`: backend contract tests (provider calls are stubbed).
- `backend/services/`, `backend/tasks/`, `infrastructure/`: broader optional/reference modules; presence does not establish operation.
- `DEPLOYMENT.md`: maintained templates and rollout checks, not proof of deployment.

## Important limitations

No production benchmark, model-accuracy measurement, compliance certification, uptime result, adoption metric, or deployment verification is asserted. Generated SQL can be wrong. Review it, confirm business definitions, and use only the synthetic playground data. The in-memory backend rate limiter is per process and uses the directly observed peer address; it is not distributed abuse protection.
