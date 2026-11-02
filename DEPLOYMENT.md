# Static public deployment and Render retirement

The maintained public demo is a Next.js **static export**, not a hosted Next server. Generation uses reviewed local query matching; SQLite executes only against bundled synthetic fixtures. No API/database service, secret, model call, editor CDN, or runtime telemetry is required. An eligible free static-hosting plan can serve this artifact with $0 recurring hosting/API/database cost. This is an architecture and deployment target, not verification of account eligibility, current spend, usage allowances, or production state.

## Existing Vercel project

Preserve the GitHub repository `cbratkovics/sql-genius-ai`, its established URL, the existing Vercel project, and its domains. Do not create a replacement account/project just for this migration.

| Setting | Value |
| --- | --- |
| Root directory | `sql-genius-frontend` |
| Framework | Next.js, static export via `output: 'export'` |
| Node | 22.x (package engines and CI both target major 22) |
| Install | `npm ci` |
| Build | `npm run build` |
| Vercel Output Directory | `.next` (Next.js build manifests; explicit in `vercel.json`) |
| Static files published | `out/` (selected by the adapter from the successful export metadata) |
| Runtime functions | None for this demo |
| Required environment variables | None |
| Rewrite/API proxy | None |

Vercel's Next.js adapter uses its Output Directory setting to locate Next build manifests, **not** as a direct static-file publish path. Keep the Next.js framework preset and `.next` setting (matching the default Next `distDir`). The adapter reads `.next/routes-manifest.json` and the successful `.next/export-detail.json`, then publishes the exported `out/` files. Pointing the adapter at `out` produces the missing `out/routes-manifest.json` error because that directory contains exported HTML/assets, not Next build manifests. Do not copy manifests into `out`, change `distDir`, or remove `output: 'export'` to address this error. See the [official adapter implementation](https://github.com/vercel/vercel/blob/main/packages/next/src/index.ts).

Confirm the existing project's framework preset remains **Next.js** and its Output Directory resolves to **`.next`**, as declared by `vercel.json`; remove any conflicting override selecting `out`. Other static hosts and `npm run preview` still serve **`out/`** directly. Local validation of the export and manifest paths is separate from a successful Vercel build; inspect the next non-production preview before claiming the hosted failure is resolved.

Review/remove legacy **project-level** rewrite/proxy overrides and disable Analytics/Speed Insights or other injected runtime scripts. Remove obsolete frontend provider/API variables from this project's build configuration only after checking their scope; do not revoke shared credentials. Clear build overrides that bypass `prebuild`, which prepares matching SQLite WASM. Keep the current project/domain assignment so the existing URL remains stable.

`vercel.json` defines static hosting headers, including same-origin `connect-src`, no frames, no objects, and restricted permissions. CSP allows `wasm-unsafe-eval` for sql.js plus inline scripts/styles needed by the generated Next hydration and existing styling. It does not allow general eval or external scripts. These headers are tested by the local preview; verify the actual deployment's response headers too. Other hosts must apply equivalent headers themselves. `next.config` server header hooks would not apply to static files.

`trailingSlash: true` creates portable `demo/index.html` and `metrics/index.html`. Confirm the host redirects `/demo` and `/metrics` to their directory routes and supports direct refresh. There are no Next image optimizer or server route dependencies. GitHub Pages and its repository subpath are not configured.

## Local acceptance and evidence

Use Node 22 and run from `sql-genius-frontend`:

```bash
npm ci
npm test
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:static
# For manual inspection of the actual export:
npm run preview
```

If a managed environment blocks browser downloads, an installed compatible Chromium can be selected with `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium`. This changes only the test binary, not package verification or networking policy. `npm run preview` serves actual `out/` files with the hosting headers; `next dev` and `next start` are not static acceptance servers.

The browser suite sets its request policy before first navigation. Cross-origin, API, and WebSocket dependencies fail the run; no fake backend responses are supplied. It records request lists in `test-results/static-results.json`, checks all maintained pages and direct refresh, exercises schema switching and real SQLite, generator states, SQL edits/provenance, policy rejection, row/byte bounds, and CSV safety. Core operations run with the browser offline after initial loading. Local results do not establish CI, production, or billing results. Only `out/` is deployed, not `.next/server` build intermediates; inspect the Vercel deployment output to confirm no functions were provisioned.

## CI and historical optional infrastructure

- `ci-frontend.yml`: standard hosted runner; frozen install, unit tests, lint, types, static export, browser checks and evidence artifact. No deploy/provider credentials.
- `ci-backend.yml`: retained Python quality/test workflow; no frontend or hosted provider requirement. It is not evidence that optional backend checks currently pass.
- `ci-container.yml`: scoped backend container build on a standard runner with `push: false`; no registry login or deployment.
- The prior Docker CI/CD and legacy security/deployment workflows are preserved as `.disabled` reference files under `infrastructure/examples/workflows/`. They are not runnable GitHub workflows. They included image publication, release/docs publication, external security integrations and deployment-related actions; no claim about their historical charges is made. Existing Python implementation, tests, Docker, monitoring, and AWS references are retained.
- The root Render blueprint moved to `infrastructure/examples/render.optional.yaml` and disables `autoDeploy`. It is a historical optional example with unverified plan assumptions, not the public deployment path. Moving it does **not** disable a live Render service, its auto-deploy hooks, or its billing.

## Owner rollout and retirement checklist

1. Review the draft PR and deploy only after owner approval. Use the reviewed frontend through the existing Vercel project on an eligible Hobby account. Check free-plan terms and spending/usage settings; avoid paid add-ons or automatic upgrades.
2. At the **real established public URL**, inspect network requests and headers, block Render and provider/database hosts, and repeat the generator/execution/CSV checks. Test `/`, `/demo/`, `/metrics/`, direct refresh, WASM, and offline core use. Confirm no server functions, hidden proxy, analytics injection, or credential requirement. Keep Render until this passes.
3. Privately identify and preserve any important Postgres data, backups, and connection/dependency inventory. Never put live data or secrets into this repository or public fixtures. Check for other users/services of the matching database and API.
4. After public verification and data preservation, disable live Render auto-deploy hooks and retire the matching Render API and Postgres resource. Separately check any related disks, Redis/worker/monitoring services and add-ons. A successful local export is not authorization or proof of safe database deletion.
5. Confirm no recurring Render billing remains in the owner dashboard/invoices, and verify Vercel usage stays within the chosen free plan. Do not revoke shared credentials without an independent dependency review.

The release-review follow-up authorizes a review-branch commit/push, a draft PR, ordinary CI, and the existing Vercel project’s non-production preview. It does not authorize merging, auto-merge, promoting a deployment, production deployment, account/plan changes, Render deletion, or credential revocation. Check the final handoff for actual publication results; a local check is not a hosted-preview result.

Proposed GitHub About copy, to apply manually after review:

> Browser-based SQL analytics playground with synthetic schemas, reviewed query templates, explicit SQLite execution, bounded result previews, and visible query provenance. No backend or API key required.
