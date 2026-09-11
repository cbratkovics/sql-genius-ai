# SQL Genius AI frontend

Next.js frontend for the **Natural-Language SQL and Analytics Playground**. The Generate button works locally for $0: it retrieves the closest reviewed intent for the selected schema or produces a conservative schema-aware preview/count fallback. It requires no account, API key, backend, or network request. An accepted read-only statement executes in local sql.js only after the user clicks Run. The dev/build lifecycle generates the ignored WASM runtime asset from the locked dependency; the repository does not commit the binary.

```bash
npm ci
npm run dev
npm run lint
npm run build
```

Local generation is visibly labeled with its match type, confidence, and assumptions and is never automatically executed. Result previews are capped and CSV exports quote delimiters/newlines/quotes, preserve nulls, and prefix text that spreadsheet software could interpret as a formula. A legacy optional provider route remains in the backend for compatibility, but the frontend does not call it. See the root README for boundaries and contracts.
