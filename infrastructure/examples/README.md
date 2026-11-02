# Historical optional deployment examples

These are reference architecture, outside the maintained static public-demo path. `render.optional.yaml` is the former root blueprint, retained with auto-deploy disabled and unverified historical plan names. No file here establishes an active deployment or bill. Do not apply it as part of static hosting.

`workflows/*.disabled` preserve the prior Docker CI/CD and legacy security/deployment workflows for historical review. Their extension/location prevents GitHub Actions execution. They contain external integrations and publication actions; review and narrow them before any intentional future reuse. Current frontend checks, backend checks, and a non-publishing backend container build remain in `.github/workflows/`.

The Python project, its tests, container configurations, and other infrastructure remain available for separately authorized local/reference work. No legacy services are required by the public playground. See `/DEPLOYMENT.md` for the static deployment and owner-controlled Render retirement procedure.
