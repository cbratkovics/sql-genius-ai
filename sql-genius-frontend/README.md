# SQL Genius AI frontend

Next.js frontend for the **Natural-Language SQL and Analytics Playground**. The no-key path loads deterministic schemas and curated SQL, then executes an accepted read-only statement in local sql.js only after the user clicks Run. The dev/build lifecycle generates the ignored WASM runtime asset from the locked dependency; the repository does not commit the binary.

```bash
npm ci
npm run dev
npm run lint
npm run build
```

Live generation is optional and calls the backend with the full selected schema structure and SQLite dialect. Provider output is visibly distinct from curated examples and is never automatically executed. Result previews are capped and CSV exports quote delimiters/newlines/quotes, preserve nulls, and prefix text that spreadsheet software could interpret as a formula. See the root README for boundaries and contracts.
