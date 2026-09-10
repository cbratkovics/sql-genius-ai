# Deployment notes

The repository contains Render, Docker, and Vercel-oriented configuration. These files are maintained templates, not evidence that a service is currently deployed or that candidate URLs are owned, current, or healthy.

Pull-request CI builds the checked-in `Dockerfile.backend` without logging in or pushing an image. Registry credentials and image publication are reserved for non-PR workflow runs.

The lowest-dependency experience is the Next.js sample playground. Its build prepares `public/sql-wasm.wasm` from the locked `sql.js` dependency, and curated queries need no provider key. Optional live generation needs the FastAPI service and server-only `ANTHROPIC_API_KEY`; configure `ANTHROPIC_MODEL` when intentionally changing models. Do not expose this key through `NEXT_PUBLIC_*` variables.

Before rollout:

1. Run the exact test/build commands in `README.md` on the deployment commit.
2. Confirm the frontend proxy/API base reaches the mounted `/api/v1/demo/sql-generate` route.
3. Verify curated query selection and explicit local execution with networking disabled.
4. Verify missing-key, upstream failure, and malformed-response UI states remain errors.
5. Confirm the prebuild step prepares `sql-wasm.wasm`, that it is served with the frontend, and that it matches the locked `sql.js` package.
6. Review CORS, hosts, secrets, database startup behavior, and per-process rate-limit limitations for the target environment.
7. Independently check `/health` and a non-secret generation request only after deployment is authorized.

The previously cited Vercel and Render URLs remain unverified candidates and are intentionally not declared canonical here. This task did not deploy or contact them.
