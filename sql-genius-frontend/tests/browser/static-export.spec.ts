import { test, expect, type Page } from '@playwright/test';
import { readFile, readdir, stat } from 'node:fs/promises';
import { resolve } from 'node:path';

// Installed before any navigation. Never fake a backend or provider response.
test.beforeEach(async ({ context }, testInfo) => {
  const requests: string[] = [];
  const unexpected: string[] = [];
  const violations: string[] = [];
  const pageErrors: string[] = [];
  await context.exposeBinding('reportCspViolation', (_, violation: string) => violations.push(violation));
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    requests.push(`${route.request().method()} ${url.href}`);
    // Every allowed browser request must map to an actual exported file/directory.
    const file = resolve('out', `.${decodeURIComponent(url.pathname)}`);
    const insideExport = file === resolve('out') || file.startsWith(`${resolve('out')}/`);
    const isStatic = insideExport && await stat(file).then(() => true, () => false);
    if (url.origin !== 'http://127.0.0.1:4173' || /^\/api(?:\/|$)/.test(url.pathname) || route.request().method() !== 'GET' || !isStatic) {
      unexpected.push(url.href);
      await route.abort('blockedbyclient');
    } else {
      await route.continue();
    }
  });
  context.on('page', page => {
    page.on('websocket', socket => unexpected.push(socket.url()));
    page.on('pageerror', error => pageErrors.push(error.message));
  });
  await context.addInitScript(() => {
    window.addEventListener('securitypolicyviolation', event => {
      void (window as unknown as Window & { reportCspViolation: (message: string) => Promise<void> })
        .reportCspViolation(`${event.effectiveDirective}: ${event.blockedURI}`);
    });
  });
  // Store evidence per test using fixtures below, including failed requests.
  evidence.set(testInfo.testId, { requests, unexpected, violations, pageErrors });
});

const evidence = new Map<string, { requests: string[]; unexpected: string[]; violations: string[]; pageErrors: string[] }>();
test.afterEach(async ({}, testInfo) => {
  const record = evidence.get(testInfo.testId)!;
  await testInfo.attach('runtime-requests', { body: JSON.stringify(record, null, 2), contentType: 'application/json' });
  expect(record.unexpected, 'No cross-origin, API, or WebSocket runtime dependency').toEqual([]);
  expect(record.violations, 'No CSP violations on any visited page').toEqual([]);
  expect(record.pageErrors, 'No uncaught browser errors').toEqual([]);
  evidence.delete(testInfo.testId);
});

async function openPlayground(page: Page) {
  await page.goto('/demo/');
  await expect(page.getByLabel('Schema:', { exact: true })).toHaveValue('ecommerce');
  await expect(page.getByRole('button', { name: 'Select reviewed SQL locally' })).toBeDisabled();
}
async function executeSQL(page: Page, sql: string) {
  await page.getByRole('textbox', { name: 'Generated SQL', exact: true }).fill(sql);
  await page.getByRole('button', { name: 'Execute', exact: true }).click();
}

test('all maintained routes and refresh use exported HTML and hosting headers', async ({ page, request }) => {
  for (const [path, heading] of [['/', 'Ask a clearer question.'], ['/demo/', 'SQL Playground'], ['/metrics/', 'Evidence, not activity estimates']]) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(200);
    const hosting = JSON.parse(await readFile('vercel.json', 'utf8'));
    for (const { key, value } of hosting.headers[0].headers) {
      expect(response?.headers()[key.toLowerCase()], `Applied ${key} on ${path}`).toBe(value);
    }
    expect(response?.headers()['x-frame-options']).toBe('DENY');
    await expect(page.getByRole('heading', { level: 1 })).toContainText(heading);
    expect((await page.reload())?.status()).toBe(200);
  }
  for (const path of ['/demo', '/metrics']) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(200);
    expect(new URL(page.url()).pathname).toBe(`${path}/`);
  }
  const wasm = await request.get('/sql-wasm.wasm');
  expect(wasm.headers()['content-type']).toBe('application/wasm');
  expect(await wasm.body()).toEqual(await readFile('node_modules/sql.js/dist/sql-wasm.wasm'));
  expect((await request.post('/api/v1/demo/sql-generate', { data: {} })).status()).toBe(405);
  expect((await request.get('/missing-route')).status()).toBe(404);
  expect((await readdir('out')).sort()).toEqual(expect.arrayContaining(['index.html', 'demo', 'metrics', 'sql-wasm.wasm']));
  // output: export is the authority; inspect the generated export manifest too.
  const exported = JSON.parse(await readFile('.next/export-detail.json', 'utf8'));
  expect(exported.success).toBe(true);
  expect(exported.outDirectory).toBe(resolve('out'));
  const exportFiles = await readdir('out', { recursive: true });
  expect(exportFiles.filter(path => /(^|\/)(api|.*\.func)(\/|$)/.test(path))).toEqual([]);
  const manifest = JSON.parse(await readFile('.next/prerender-manifest.json', 'utf8'));
  expect(Object.keys(manifest.dynamicRoutes)).toEqual([]);
});

test('curated and locally matched SQL execute with provenance and safe CSV', async ({ page }) => {
  await openPlayground(page);
  await page.getByRole('tab', { name: 'Sample Queries', exact: true }).click();
  await page.getByRole('button', { name: /^Show me all products/ }).click();
  await expect(page.getByRole('heading', { name: 'Query Results', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Execute', exact: true }).click();
  await expect(page.getByRole('table')).toContainText('Laptop Pro');
  await expect(page.getByText('Executed locally with SQLite · curated SQL', { exact: true })).toBeVisible();
  await page.getByText('Execution provenance', { exact: true }).click();
  await expect(page.locator('details')).toContainText('SELECT * FROM products');

  await page.getByLabel('Natural Language Query').fill('Show me all customers');
  await page.getByRole('button', { name: 'Select reviewed SQL locally' }).click();
  await expect(page.getByText('Status: supported.', { exact: false })).toBeVisible();
  await expect(page.getByRole('table')).toHaveCount(0);
  await page.getByRole('button', { name: 'Execute', exact: true }).click();
  await expect(page.getByRole('table')).toContainText('customer_id');

  await executeSQL(page, `SELECT 'a,b' AS name, 0 AS zero, NULL AS empty, '=2+2' AS formula, 'a"b' AS quote, 'line' || char(10) || 'break' AS multiline;`);
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('query-results.csv');
  const csv = await readFile((await download.path())!, 'utf8');
  expect(csv).toBe('"name","zero","empty","formula","quote","multiline"\r\n"a,b","0",,"\'=2+2","a""b","line\nbreak"');
  await page.getByRole('textbox', { name: 'Generated SQL', exact: true }).fill('SELECT 42 AS changed;');
  await expect(page.getByRole('table')).toHaveCount(0);
  await expect(page.getByText('Execution provenance', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Generation details', exact: true })).toHaveCount(0);
});

test('clarifications and unsupported conclusions never produce answer SQL', async ({ page }) => {
  await openPlayground(page);
  const input = page.getByLabel('Natural Language Query');
  const sql = page.getByRole('textbox', { name: 'Generated SQL', exact: true });
  await input.fill('Who are our best customers?');
  await page.getByRole('button', { name: 'Select reviewed SQL locally' }).click();
  await expect(page.getByText('Status: clarification.', { exact: false })).toBeVisible();
  await expect(sql).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Execute', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: /^Observed completed-order value/ }).click();
  await expect(sql).toHaveValue(/status = 'delivered'/);
  await page.getByRole('button', { name: 'Execute', exact: true }).click();
  await expect(page.getByRole('table')).toContainText('metric_value');
  for (const [question, state] of [['Show product profitability', 'unsupported'], ['Show me all products but not Electronics', 'clarification']]) {
    await input.fill(question);
    await page.getByRole('button', { name: 'Select reviewed SQL locally' }).click();
    await expect(page.getByText(`Status: ${state}.`, { exact: false })).toBeVisible();
    await expect(sql).toHaveValue('');
    await expect(page.getByRole('table')).toHaveCount(0);
  }
});

test('offline schema switching and SQLite execution retain policy and preview bounds', async ({ page, context }) => {
  await openPlayground(page);
  await page.getByRole('tab', { name: 'Schema Templates', exact: true }).click();
  const templates = page.getByRole('tabpanel');
  await expect(templates).toContainText('E-commerce Platform');
  await expect(templates.getByText('products', { exact: true })).toBeVisible();
  await expect(templates.getByText('orders', { exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Playground', exact: true }).click();
  await page.waitForLoadState('networkidle');
  const record = evidence.get(test.info().testId)!;
  const before = record.requests.length;
  await context.setOffline(true);
  const schema = page.getByLabel('Schema:', { exact: true });
  for (const [id, table] of [['saas', 'organizations'], ['healthcare', 'patients'], ['finance', 'accounts'], ['social', 'users'], ['ecommerce', 'products']]) {
    await schema.selectOption(id);
    await expect(schema).toHaveValue(id);
    await executeSQL(page, `SELECT COUNT(*) AS fixture_rows FROM ${table};`);
    await expect(page.getByRole('table').locator('tbody td')).toHaveText(/[1-9]\d*/);
  }
  for (const blocked of ['DELETE FROM products;', 'SELECT 1; SELECT 2;']) {
    await executeSQL(page, blocked);
    await expect(page.getByText(/Query blocked:/).last()).toBeVisible();
    await expect(page.getByRole('table')).toHaveCount(0);
  }
  await executeSQL(page, 'WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<501) SELECT x FROM n;');
  await expect(page.getByText('500 preview rows (truncated)', { exact: true })).toBeVisible();
  await expect(page.getByRole('table').locator('tbody tr')).toHaveCount(500);
  await executeSQL(page, 'SELECT hex(zeroblob(500001)) AS oversized;');
  await expect(page.getByText(/1 MB collection limit/).last()).toBeVisible();
  await expect(page.getByRole('table')).toHaveCount(0);
  await page.getByLabel('Natural Language Query').fill('Show me all products');
  await page.getByRole('button', { name: 'Select reviewed SQL locally' }).click();
  await page.getByRole('button', { name: 'Execute', exact: true }).click();
  await expect(page.getByRole('table')).toContainText('Laptop Pro');
  const offlineDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV', exact: true }).click();
  expect((await offlineDownload).suggestedFilename()).toBe('query-results.csv');
  expect(record.requests.slice(before), 'Core operations issue no requests after loading').toEqual([]);
  await context.setOffline(false);
});

for (const [name, viewport] of [
  ['desktop', { width: 1280, height: 720 }],
  ['mobile', { width: 390, height: 844 }],
] as const) {
  test(`${name}: notifications stay in flow during normal pointer and keyboard use`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await openPlayground(page);
    const schema = page.getByLabel('Schema:', { exact: true });
    // Real actions recreate the previously obstructing stack; no mocked toasts.
    for (const id of ['saas', 'healthcare', 'finance', 'social', 'ecommerce', 'saas', 'healthcare', 'finance', 'social', 'ecommerce']) {
      await schema.selectOption(id);
    }
    const status = page.getByRole('status', { name: 'Playground notifications' });
    await expect(status).toContainText('E-commerce');
    await expect(page.getByRole('status')).toHaveCount(1);

    await executeSQL(page, 'SELECT 7 AS pointer_result;');
    await expect(page.getByRole('table')).toContainText('pointer_result');
    await expect(status).toContainText('Query executed successfully');
    await executeSQL(page, 'DELETE FROM products;');
    await expect(status).toContainText('Query blocked:');
    await status.scrollIntoViewIfNeeded();
    // Actual hit-testing confirms that the error is readable, not covered by an overlay.
    const readable = await status.evaluate(element => {
      const rect = element.getBoundingClientRect();
      return element.contains(document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2));
    });
    expect(readable).toBe(true);
    await expect(page.getByRole('table')).toHaveCount(0);

    await page.getByRole('textbox', { name: 'Generated SQL', exact: true }).fill('SELECT 9 AS keyboard_result;');
    const execute = page.getByRole('button', { name: 'Execute', exact: true });
    await execute.focus();
    await execute.press('Enter');
    await expect(page.getByRole('table')).toContainText('keyboard_result');
    await expect(status).toContainText('Query executed successfully');
    await expect(page.locator('[data-rht-toaster]')).toHaveCount(0);
    await test.info().attach(`${name}-notifications`, { body: await page.screenshot(), contentType: 'image/png' });
  });
}
