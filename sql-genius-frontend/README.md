# SQL Genius AI static frontend

The maintained public playground matches questions to reviewed query templates, labels ambiguous/unsupported/exploratory requests, and executes accepted read-only SQL in real browser SQLite only after **Execute**. No account, API key, hosted database, provider fallback, editor CDN, or runtime analytics is used. Editable SQL uses a labeled native textarea with keyboard and focus support. The latest operation notification appears in normal layout beside the SQL controls, so stacked messages cannot cover inputs, results, or errors.

Use Node 22.x (matching CI and the Vercel build major):

```bash
npm ci
npm run dev
```

Development uses Webpack so the existing sql.js browser fallbacks apply. Production is a portable static export with directory-style routes:

```bash
npm test
npm run lint
npm run typecheck
npm run build
npm run preview
```

`out/` is the complete deployment artifact. The preview serves `out/` on port 4173 (`PORT` can override it), applies the all-route Vercel security headers, and returns real 404s rather than a single-page-app fallback. Do not use `next start`. `predev`/`prebuild` copy WASM from the locked sql.js dependency to the ignored public runtime path; the export includes that file.

```bash
npx playwright install chromium
npm run test:static
```

The browser tests launch the static preview, install a request policy before navigation, fail unexpected cross-origin or API requests, record request evidence, validate CSP/WASM, and execute core operations offline after loading assets. If downloading Chromium is unavailable but a compatible binary exists, set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` to its absolute path. CI installs Playwright Chromium on a standard runner. Test reports are ignored local outputs under `test-results/`.

Deploy the reviewed artifact to the existing Vercel project/URL on an eligible Hobby account: root `sql-genius-frontend`, `npm run build`, output `out`. `vercel.json` supplies static hosting headers and no proxy rewrites or functions. It must be configured at the hosting layer on other hosts too. CSP permits same-origin connections, WebAssembly compilation, Next's inline hydration scripts, and inline styles; it does not allow general JavaScript eval, external scripts, frames, or workers. The browser suite tests these headers against the actual export. Dashboard-level Vercel Analytics/Speed Insights injection must remain disabled and needs verification at the real URL.

Preview results are capped at 500 rows and 1,000,000 collected UTF-8 bytes; CSV exports quote delimiters/newlines/quotes, preserve nulls, and prefix formula-like text. SQLite executes on the main thread with no hard CPU cancellation. Only bundled synthetic databases are supported. The optional Python project is retained outside this production graph. See the root README and DEPLOYMENT.md for evidence and retirement steps.
