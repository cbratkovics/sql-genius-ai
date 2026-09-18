# Architecture and validation

## Supported workflow

SQL Genius AI is a SQL analytics and decision-support playground for bundled synthetic data. The maintained browser path loads a versioned fixture, matches questions to reviewed templates, asks for clarification when a definition changes the answer, exposes exact SQL for review, and executes only after the user chooses **Execute**. Unsupported questions and exploratory previews are labeled separately.

The flagship e-commerce question, “Who are our best customers?”, requires a choice between observed completed-order value and completed-order frequency. Both definitions use delivered order headers from 2024-06-01 through 2024-06-15. The SQL aggregates headers before ranking, so a join to multiple order-item rows cannot multiply an order total.

## Data and metric boundaries

Tables expose their row grain, fixture coverage, keys, child-to-parent relationship cardinality, version, and synthetic provenance. `customers.total_spent` is a separate snapshot whose coverage is not asserted to equal the included order headers. Order line count, physical units (`SUM(quantity)`), distinct products, and order-header value are separate measures. Gross line-item sales are not profit because the fixture has no product costs.

The SaaS activity examples use the explicit analysis date 2024-07-01. The inactivity classification is a deterministic illustration, not a churn model; missing activity is a separate state. Unique feature users are a count, not an adoption rate, and current subscription status is a snapshot rather than a conversion funnel.

## Execution and validation

The read-only policy accepts one SELECT or read-only CTE before SQLite prepares the statement. This is a narrow product control, not a security sandbox. Preview collection is capped at 500 rows and 1,000,000 UTF-8 bytes. CSV export uses the executed result snapshot and escapes spreadsheet formulas. Schema loading builds a new database before exposing it and clears readiness after a failed load.

Run:

```bash
cd sql-genius-frontend
npm ci
npm test
npm run lint
npx tsc --noEmit
npm run build
```

Tests independently check line count versus units, parent/child fan-out, relationship metadata, question-state behavior, SQL policy and CSV handling, and execute every e-commerce curated query against the fixture.

## Limitations

The fixtures are small and synthetic. A successful query is not evidence of production accuracy or business impact. Browser SQL runs synchronously on the main thread with no hard CPU cancellation. A bounded preview is not a complete population export. Arbitrary edited SQL has no guided business conclusion. The optional provider-backed FastAPI route is separate from the no-key browser workflow and is not evidence that a provider or hosted deployment is active.
