# Portfolio evidence and external alignment

## Evidence categories

- **Inspected:** the mounted FastAPI routers, browser database, schema/query fixtures, provider wrapper, optional services, CI, environment examples, and deployment templates.
- **Executed:** frontend lint/type/build checks and focused policy/CSV tests. The curated workflow uses real browser SQLite on synthetic data; its page and WASM asset were HTTP-smoke-checked, but interactive execution was not browser-automated in this environment.
- **Evaluated:** contract cases cover missing credentials, malformed/fenced output, real schema context, zero token usage, and disabled remote execution. Policy implementation covers a single read-only statement, comments/literals, mutation and SQLite policy commands, and bounded previews. This is not an LLM accuracy score.
- **Unverified:** a live Anthropic request, browser interaction/worker cancellation, candidate hosted URLs, external database services, Redis/Celery operation, billing/email, and production controls.
- **Intentionally disabled:** remote demo SQL execution and fabricated aggregate metrics. The compatibility execution route returns no illustrative rows and `execution_status=not_run`.

The sample rows are synthetic. A successful local result is observed SQLite execution on those rows, not a precomputed provider result. Provider output remains `not_run` until the user explicitly runs the exact displayed SQL.

## Operational limits

The browser policy is a narrow product guard, not authorization for arbitrary databases. It rejects multiple statements and mutation/schema/attachment/extension/pragma commands, then relies on SQLite preparation for syntax/name errors. Preview collection is capped at 500 rows and 1 MB. sql.js executes synchronously on the browser main thread, so a hard CPU deadline/termination boundary was not established; trusted finite fixture databases and the query-length bound limit the maintained demo scope.

The optional rate limiter is per-process and not shared across replicas. Authentication, tenants, caching, queues, payments, backup, and observability implementations were preserved but were not promoted as active services.

## Reproducibility record

Record the source commit/dirty state with `git rev-parse HEAD` and `git status --short`, then run the commands in the root README. Provider-client tests use a stub and make no paid request; they were authored but could not run in this environment because backend dependencies were unavailable. Test names are the case identifiers and assertions define comparison rules. No `latest` live-model evaluation artifact is published because none was run.

## External follow-up (not performed)

**Proposed GitHub About (under 350 characters):** SQL Genius AI — a natural-language SQL and analytics playground for inspecting schema-aware SQL and running reviewed, read-only queries locally against deterministic SQLite sample data. Optional provider generation; explicit provenance and limitations.

**Résumé/site bullets:**

- Built a schema-aware natural-language SQL playground that separates generation from execution and runs reviewed read-only queries locally against deterministic SQLite fixtures.
- Added typed generation/execution provenance, bounded result previews, CSV-safe export, and stubbed provider contract tests without claiming unmeasured model accuracy.

Repository topics/About, résumé, site, and hosted deployments were not changed. Verify ownership, environment configuration, `/health`, no-key sample execution, provider failure behavior, mobile layout, and asset loading before publishing a canonical URL.
