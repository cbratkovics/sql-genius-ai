# Static public-demo migration — release review

Reviewed the migration from clean baseline `ac062151000422c291cf0ec803cda988c325353a` on November 2, 2026, retaining branch `review/static-public-demo` and all existing migration work. The follow-up release review authorizes committing this diff, a non-force branch push, and a draft PR against the verified default branch `main`, plus ordinary CI and the existing project’s non-production Vercel preview. The final release handoff records the commit SHA and publication result. No reset, main-branch modification, repository/remote rename, merge, production deployment, live provider request, Render mutation, account/plan change, or credential revocation is part of this release review.

## Result and scope

Next.js now emits a portable `out/` export with trailing-slash routes and the locked SQLite WASM. The Render rewrite and unused provider client/hook are removed. The only import of `src/lib/api.ts` was the unused `useDemo.ts` hook; no maintained component imported that hook. The now-unused React Query provider and corresponding packages were removed. Monaco's default CDN loader was replaced with a labeled, keyboard-editable SQL textarea; unused analytics/Axios dependencies were removed. The reviewed generator, sql.js execution engine, policy, fixture SQL/data, query hooks, CSV serializer, and collection bounds were verified byte-for-byte unchanged from the baseline. No existing locked package version was upgraded.

The maintained source has no `fetch`, Axios, WebSocket, EventSource, API-related environment-variable read, or analytics integration. sql.js loads its WASM from the same origin. External GitHub links are user navigation, not runtime dependencies. A scan of the exported artifact found no Render host, Anthropic API host, `sql-generate`, jsDelivr, Monaco, or Vercel analytics script references.

Public wording describes local reviewed matching rather than a hosted model/backend. Backend implementation/tests remain. The Render blueprint is an explicitly optional historical example, with auto-deploy disabled in that example. Both archived workflow files are preserved byte-for-byte in a non-executable location. The active frontend checks and backend quality/test checks remain; the replacement container check builds without registry authentication, publication, or deployment. The archived legacy pipelines duplicated checks (many suppressed failures) and included unrelated external integrations/publication; archiving them makes no claim about past billing.

## Commands and observed outcomes

Executed from `/workspace/sql-genius-ai/sql-genius-frontend` with Node **22.23.4** and npm **11.9.0** activated via `/workspace/.sql-genius-tools/node_modules/node/bin`. Package verification and managed proxy TLS were retained.

| Command | Local outcome |
| --- | --- |
| `npm ci` | Passed; frozen lockfile install, 432 packages |
| `npm test` | Passed: 13 tests, 0 failures/skips |
| `npm run lint` | Passed |
| `npm run typecheck` | Passed |
| `NEXT_TELEMETRY_DISABLED=1 npm run build` | Passed; export completed, `export-detail.json` reports success |
| `npx playwright install chromium` | Earlier migration attempt: download denied by policy for `cdn.playwright.dev`; not retried during release review |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:static` | Passed: 6 browser tests, 0 failures/skips/flaky results |
| `git diff --check` | Passed |

The installed **Chromium 154.0.8037.57** was used for local browser verification with Playwright 1.58.2. CI is configured to download its matching Playwright Chromium. The full `npm ci` → unit → lint → types → build → browser chain passed during release review. After adding focused schema-inspection and offline-CSV assertions, lint, types, and the complete six-test browser command passed again against the same built application. CI, any hosted Vercel preview, and production results are separate and are not established by these local commands. The package range remains Node 22+ and deployment/CI remain pinned to major 22.

The suite launches `npm run preview` using the built-in Node static server. It serves actual **`/workspace/sql-genius-ai/sql-genius-frontend/out/`**, never `next dev`, and applies the same all-route security headers stored in `vercel.json`. All maintained routes (`/`, `/demo/`, `/metrics/`), direct refresh, slash redirects, real 404s, and WASM content/type were checked. Response headers are compared with every header declared in `vercel.json` (including the full CSP, permissions, frame, referrer, and content-type policies), not just an absence of CSP violations. `.next/export-detail.json` reports a successful export; no API/function paths exist in `out/`, and the prerender manifest has no dynamic routes. `.next/server` is a build intermediate and is not the deployment artifact.

## Browser and network evidence

Detailed per-test request evidence is attached in the ignored local report `sql-genius-frontend/test-results/static-results.json`. The final complete run recorded:

| Browser test | Routed runtime requests | Unexpected destinations | CSP violations | Uncaught page errors |
| --- | ---: | ---: | ---: | ---: |
| Routes, refresh, hosting headers | 126 | 0 | 0 | 0 |
| Curated/local SQL, provenance, CSV | 20 | 0 | 0 | 0 |
| Clarification/unsupported states | 20 | 0 | 0 | 0 |
| Offline schemas, policy, bounds | 20 | 0 | 0 | 0 |
| Desktop notification regression | 20 | 0 | 0 | 0 |
| Mobile notification regression | 20 | 0 | 0 | 0 |

All 226 browser runtime requests were same-origin GETs mapping to actual files/directories in `out/`, not API calls or proxy paths. The request policy is installed before navigation and aborts/fails cross-origin requests, `/api` and `/api/` paths, non-GET methods, and requests not mapping to an exported file/directory; WebSocket events and CSP violations fail assertions too. No legacy request was replaced with a successful stub. A separate non-browser HTTP probe verifies that POST to the old API path is rejected with 405 by the static preview; this does not call a backend.

The tests execute actual curated product SQL and a supported local customer request, exercise both clarification and unsupported questions without answer SQL, verify the selected best-customer definition, and ensure edits clear stale results/generation/provenance. CSV checks cover comma, quote, newline, zero, null, and formula-like text. The schema template tab is checked for inspectable product/order tables. Offline tests load all five synthetic schemas and query real fixture rows, reject mutation/multiple statements, return exactly 500 rows with truncation, reject a result exceeding 1,000,000 bytes, and then execute another local-generation request and export CSV while offline. There were **zero additional requests during the offline core operations** after initial loading. Cold-start offline use and offline refresh are not claimed or tested. The WASM response matches the locked sql.js binary byte-for-byte.

`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_BASE_URL`, and `NEXT_PUBLIC_ANTHROPIC_API_KEY` were absent in the tested process. Their values were not inspected. The public source has no variable reads or paid fallback branch.

## Limits and owner actions

Local export, static preview, browser behavior, and hosting-header compatibility are verified. CI, the actual Vercel deployment/headers/functions, existing URL behavior, Hobby eligibility, current Render dependencies/data/plans, and actual billing are **unverified**. Backend application code, tests, and `ci-backend.yml` are unchanged; only optional-backend documentation/example comments changed. No Python tests, ruff/mypy, container build, or legacy security checks were run locally. Frontend results do not establish backend validity. Active Python checks and the build-only container check can run as ordinary PR CI; no active workflow publishes images/releases/docs, deploys, or evaluates a live provider. Archived examples do not turn off live Render auto-deploy hooks.

The toast issue was a real interaction defect, reproduced before correction on the actual export at 1280×720 desktop and 390×844 mobile sizes. Ten rapid real schema switches created eleven stacked notifications. Desktop pointer actionability failed because a toast intercepted Execute; mobile screenshots showed notifications covering inputs/editor even when Execute happened to be pointer-actionable.

The smallest targeted correction replaces the fixed global overlay with one current-operation status in normal document flow beside the SQL controls (`PlaygroundNotifications.tsx`). It retains success/error messages, four-second timing, hover pause, icons, wrapping, and a persistent polite/atomic live region. Showing the latest operation avoids an unbounded visual stack without hiding notifications only in tests. Errors are checked for visibility and actual hit-test readability. Both desktop and mobile regressions exercise real schema changes, successful normal pointer execution, a blocked mutation/error, and normal keyboard execution. The shared SQL test helper now uses normal pointer clicks; no forced click, toast removal, or test-only CSS is used. Sanitized after-fix screenshots are attached to the ignored local Playwright report, not committed. Before-fix reproduction screenshots were kept outside the repository under `/tmp`.

SQLite still runs on the main thread with no hard CPU cancellation or general sandbox guarantee.

Deploy only after owner review using the **existing Vercel project/URL**, root `sql-genius-frontend`, Node 22.x, install `npm ci`, build `npm run build`, output **`out`**, no required environment variables/functions/proxy. Keep project-level telemetry injection disabled and verify actual response headers and routing.

Owner sequence: deploy reviewed frontend → verify the real URL with Render/providers blocked → privately preserve important Postgres data and check dependents → disable live Render auto-deploy and retire the matching API/database → confirm invoices/dashboard show no recurring billing. Full settings, safety boundaries, and the proposed manual GitHub About copy are in `DEPLOYMENT.md`.

## Publication boundary

Read-only GitHub API preflight failed for both GraphQL (`Post https://api.github.com/graphql: Forbidden`) and REST (`Get https://api.github.com/repos/cbratkovics/sql-genius-ai: Forbidden`); an unauthenticated connectivity check returned `CONNECT tunnel failed, response 403`. This is an environment API-access blocker, not evidence of insufficient repository permissions. Existing HTTPS Git reads work and verify the default branch as `main`. Do not extract or replace injected credentials to bypass policy. The authorized branch push and draft-PR attempt are reported in the final handoff. If the API remains blocked, the owner can create the draft from the prepared PR text once authenticated in an allowed environment. Publication, CI, hosted preview, production, and billing must each be reported only when observed.

## Exact changed-file inventory

Deleted workflow/blueprint entries below are retained under the new historical example paths, not destroyed. Generated `out/`, WASM, caches, and test reports remain ignored.

| File | Change |
| --- | --- |
| `.env.example` | Modified |
| `.github/workflows/ci-cd-security.yml` | Removed from active location |
| `.github/workflows/ci-frontend.yml` | Modified |
| `.github/workflows/docker-ci-cd.yml` | Removed from active location |
| `DEPLOYMENT.md` | Modified |
| `README.md` | Modified |
| `backend/.env.example` | Modified |
| `backend/README.md` | Modified |
| `docs/PORTFOLIO_EVIDENCE.md` | Modified |
| `render.yaml` | Removed from active location |
| `sql-genius-frontend/.gitignore` | Modified |
| `sql-genius-frontend/README.md` | Modified |
| `sql-genius-frontend/next.config.ts` | Modified |
| `sql-genius-frontend/package-lock.json` | Modified |
| `sql-genius-frontend/package.json` | Modified |
| `sql-genius-frontend/src/app/layout.tsx` | Modified |
| `sql-genius-frontend/src/app/page.tsx` | Modified |
| `sql-genius-frontend/src/components/MetricsDashboard.tsx` | Modified |
| `sql-genius-frontend/src/components/SQLPlayground.tsx` | Modified |
| `sql-genius-frontend/src/components/PlaygroundNotifications.tsx` | Added |
| `sql-genius-frontend/src/hooks/useDemo.ts` | Removed from active location |
| `sql-genius-frontend/src/lib/api.ts` | Removed from active location |
| `sql-genius-frontend/vercel.json` | Modified |
| `.github/workflows/ci-container.yml` | Added |
| `docs/STATIC_MIGRATION.md` | Added |
| `infrastructure/examples/README.md` | Added |
| `infrastructure/examples/render.optional.yaml` | Added |
| `infrastructure/examples/workflows/ci-cd-security.yml.disabled` | Added |
| `infrastructure/examples/workflows/docker-ci-cd.yml.disabled` | Added |
| `sql-genius-frontend/playwright.config.ts` | Added |
| `sql-genius-frontend/scripts/preview-static.mjs` | Added |
| `sql-genius-frontend/tests/browser/static-export.spec.ts` | Added |

## Node 22 build-major follow-up — November 2, 2026

Based on reviewed commit `4a70d307d50855bd3382716ba3fc2a65dd7de1ae` on `review/static-public-demo`, with existing draft PR #6 against `main`. Pinned `engines.node` to `22.x` in the package and corresponding root lockfile metadata, and corrected the root/frontend README and deployment requirement. This supersedes the historical Node 22+ range recorded above; earlier validation records are preserved. Application implementation and tests are unchanged. Comparing both manifests with the reviewed commit confirms only the root engine field changed; all locked dependency versions and metadata remain identical.

Using **Node 22.23.4 / npm 11.9.0**, ran from `sql-genius-frontend`:

```bash
npm ci
npm test
npm run lint
npm run typecheck
NEXT_TELEMETRY_DISABLED=1 npm run build
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:static
```

All passed locally: 13 unit tests, lint, types, successful static export to `out/`, and 6 browser tests with no failures/skips. `git diff --check` passed. Vercel should select **Node 22.x**. No dependency upgrade, application change, or test change was required.

**Remote evidence boundary:** the owner reports Vercel deployment `dpl_Bs5WFEcusaXy8Dfr11idJ71Ep2TG` failed for the previous reviewed commit. Its underlying build error has not been established, and no actual Vercel build log was available. The read-only PR #6 status query returned `Post "https://api.github.com/graphql": Forbidden`; GitHub CI and current hosted-preview status were not independently observed. No PR creation was retried. This local Node-range correction is not evidence that the reported Vercel failure is fixed. Production behavior and billing remain unverified and owner-controlled; no deployment promotion, infrastructure deletion, or account-plan change was performed.

## Vercel manifest-directory correction — November 2, 2026

The owner supplied the actionable error that `sql-genius-frontend/out/routes-manifest.json` could not be found. The earlier Vercel Output Directory guidance was incorrect for the **Next.js framework adapter**: its `outputDirectory` selects the Next build-manifest directory, not the exported static publish directory. The [official adapter source](https://github.com/vercel/vercel/blob/main/packages/next/src/index.ts) reads manifests there, then detects successful export metadata and selects its `outDirectory` for static output. Local inspection confirmed the manifest exists in `.next/` and correctly does not exist in `out/`. This is a separate configuration issue from the preceding Node-major pin.

Changed only `vercel.json`'s Output Directory from `out` to **`.next`** and corrected current deployment guidance in the root/frontend README and `DEPLOYMENT.md`. This supersedes earlier Vercel output-directory instructions while retaining their historical validation results. Keep the existing project, Next.js framework preset, root `sql-genius-frontend`, Node 22.x, and build `npm run build`. The app retains `output: 'export'`; direct static hosting and local preview still serve **`out/`**. No application/test code, dependency manifest, locked version, or Next configuration changed; no manifests were copied into the export.

Using Node **22.23.4 / npm 11.9.0**, reran from `sql-genius-frontend`: `npm test` (13 passed), `npm run lint`, `npm run typecheck`, `NEXT_TELEMETRY_DISABLED=1 npm run build`, and `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium npm run test:static` (6 passed, no failures/skips). All passed. Verified the configured `.next/routes-manifest.json` exists, `.next/export-detail.json` reports success and selects `out/`, all maintained exported pages exist, and exported WASM matches the locked dependency byte-for-byte. `git diff --check` passed. The installed dependencies were reused; no install or upgrade was needed. An initial command ran from the repository root and failed because there is no root package.json; the reported successful checks ran from the frontend directory.

This corrects the diagnosed local configuration mismatch, not a verified hosted deployment. GitHub CI and a new Vercel preview result remain unobserved at this handoff; the prior GitHub API access restriction has not been bypassed. No new PR or production deployment was created, no security check was disabled, and production/billing/Render retirement remain owner-controlled. Verify the next existing-project non-production preview and diagnose any newly reported first actionable error separately.

## Bounded backend CI triage — November 2, 2026

**External verification supplied by the owner:** Vercel deployment and static frontend CI (including `npm run test:static`) succeeded for `898b5b8ffb63d394ca5390b009ea233e0f204e18`. Backend run `41533246447`, job `125578560334`, failed at `ruff check .`; its mypy and pytest steps were skipped. These are supplied remote results, not fresh API observations. Hosted functional behavior, production rollout, and billing are not established by deployment/build success. All working hosting settings remain untouched: Next.js framework, root `sql-genius-frontend`, Vercel Output Directory `.next`, Node 22.x, Next `output: 'export'`, portable export `out/`.

### Lint reproduction and version boundary

Inspected the unchanged `ci-backend.yml`: Python 3.11, working directory `backend`, requirements install followed by **unpinned** `pip install ruff pytest mypy`, then `ruff check .`. No repository Ruff configuration is present. Job-log retrieval returned `Forbidden` for the GitHub API. The exact Ruff version installed in that job is therefore **not yet verified**; the owner can supply its installation line or activate `api.github.com` network access. A narrowly scoped environment draft addition was saved for that host; draft persistence alone does not activate access.

For a controlled local comparison, the workflow's unpinned Ruff requirement resolved to **Ruff 0.17.3** under isolated Python **3.11.17**. Ran the actual `ruff check .` from both `/workspace/sql-genius-ai/backend` at `898b5b8` and a detached temporary worktree at `/tmp/sql-genius-ci-baseline/backend`, baseline `ac062151000422c291cf0ec803cda988c325353a`. The same executable and default configuration were used; only cache paths differed, outside the checkouts. Both commands exited **1**, reporting **633 diagnostics in 37 files**. Compared JSON diagnostics, resolved settings, and linted file lists after normalizing checkout/cache prefixes: all match exactly, including messages, locations, fixes, and selected rules. Under this measured version/configuration, **0 diagnostics are introduced by the PR** and all 633 are already present in the baseline. This is an executed comparison, not an inference from unchanged application files.

Rule counts: `UP006=182`, `UP045=103`, `BLE001=101`, `B008=47`, `DTZ003=47`, `I001=37`, `RUF013=35`, `UP035=32`, `TRY002=18`, `TRY201=10`, `RUF059=4`, `RUF010=4`, `SIM102=3`, `UP007=2`, `SIM117=2`, `ASYNC230=2`, and one each of `PERF102`, `PIE790`, `LOG014`, `RUF022`. First exact diagnostics include:

```text
api/auth.py:1:1: I001 Import block is un-sorted or un-formatted
api/auth.py:23:19: UP045 Use `X | None` for type annotations
api/auth.py:50:24: B008 Do not perform function call `Depends` in argument defaults; instead, perform the call within the function, or read the default from a module-level singleton variable
api/auth.py:63:15: TRY201 Use `raise` without specifying exception name
api/auth.py:64:12: BLE001 Do not catch blind exception: `Exception`
```

Exact complete diagnostics/settings were retained as local evidence outside the repository under `/workspace/sql-genius-ci-evidence/`; no raw test logs or generated outputs are committed. The normalized 633-line diagnostic list has SHA-256 `0c7583713065a2c20a259d6afeff92716a0fbe6286ac866cbb18144627ec7949`. No repository configuration drift was found. Because Ruff is unpinned and the failed job's version is unavailable, tool-version drift in that specific run is **unconfirmed**, not asserted as its cause. The comparison must be repeated if its logged version differs from 0.17.3.

### Independent backend tests

Installed `backend/requirements.txt` in an external Python 3.11.17 virtual environment without changing dependency declarations. Test versions: pytest 7.4.4, pytest-asyncio 0.23.3, FastAPI 0.109.0, SQLAlchemy 2.0.25, HTTPX 0.26.0, Passlib 1.7.4, transitive bcrypt 5.0.0. Installation completed; pip also reported an isolated seed-tool conflict between wheel 0.48.0 and the requirements-resolved packaging 23.2. No dependency workaround was applied to the repository.

Ran the following pytest targets from each checkout's `backend` directory through the same external offline harness, with `PYTHONPATH` pointing to that checkout. The harness forces in-memory SQLite, removes provider credentials, rejects outbound INET connections/DNS, and makes SMTP sending fail explicitly; provider generation in the contract suite is stubbed by the existing tests. No paid provider, mail delivery, or hosted/production database was used.

| Target | Head | Baseline |
| --- | --- | --- |
| `pytest -q test_demo_contract.py` | 9 passed | 9 passed |
| `pytest -q` (workflow target) | Exit 3 during collection; no completed suite | Same |
| `pytest -q tests` (account subset) | 4 passed, 2 failed, 16 fixture errors | Same test IDs and counts |

The full target raises `sqlalchemy.exc.InvalidRequestError: Table 'tenants' is already defined for this MetaData instance` during collection on both commits. The isolated account target exposes a Passlib/bcrypt backend-probe `ValueError: password cannot be longer than 72 bytes`, later `UNIQUE constraint failed: tenants.slug` fixture errors, registration returning 500 instead of 200, and unauthorized access returning 403 instead of the expected 401. These are observed baseline failures under the identical local dependencies, not new migration defects. The bcrypt issue involves an unconstrained transitive dependency; it is separate from the Ruff step that actually failed remotely. Local mypy was not run; remote mypy/pytest were skipped and cannot be described as passing.

### Disposition

No introduced lint failure or backend code correction was identified under the measured toolchain. Do not mass-fix the 633 findings, add ignores, weaken rules, suppress failures, or disable backend CI in this static-hosting PR. A separate backend follow-up should establish/pin the intended Ruff version and configuration, remediate the existing lint debt, and diagnose test collection, compatible test dependencies, fixture isolation, and HTTP contract failures in reviewable changes.

Backend CI remains red and is a release/review blocker if required by branch protection; required-check policy has not been independently inspected. Static deployment/frontend CI success does not waive that check or validate the optional backend. This triage changes documentation only; no production deployment, merge, Render/account change, or working deployment setting is changed. Exact failed-run version matching remains pending access or the job's installation log.
