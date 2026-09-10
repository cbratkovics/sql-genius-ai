const MAX_QUERY_CHARS = 20_000;

export interface PolicyResult {
  accepted: boolean;
  reason?: string;
}

/** Strip comments and literals without interpreting their contents as SQL tokens. */
function codeOnly(sql: string): { code: string; statements: number } {
  let code = '';
  let state: 'code' | 'single' | 'double' | 'line' | 'block' = 'code';
  let statements = 0;
  for (let i = 0; i < sql.length; i += 1) {
    const c = sql[i];
    const n = sql[i + 1];
    if (state === 'line') {
      if (c === '\n') { state = 'code'; code += ' '; }
      continue;
    }
    if (state === 'block') {
      if (c === '*' && n === '/') { state = 'code'; i += 1; code += ' '; }
      continue;
    }
    if (state === 'single') {
      if (c === "'" && n === "'") { i += 1; continue; }
      if (c === "'") state = 'code';
      continue;
    }
    if (state === 'double') {
      // Quoted identifiers stay opaque to keyword checks.
      if (c === '"' && n === '"') { i += 1; continue; }
      if (c === '"') state = 'code';
      continue;
    }
    if (c === '-' && n === '-') { state = 'line'; i += 1; continue; }
    if (c === '/' && n === '*') { state = 'block'; i += 1; continue; }
    if (c === "'") { state = 'single'; code += ' '; continue; }
    if (c === '"') { state = 'double'; code += ' '; continue; }
    if (c === ';') { statements += 1; code += ' '; continue; }
    code += c;
  }
  if (state === 'single' || state === 'double' || state === 'block') {
    throw new Error('Unterminated SQL literal, identifier, or comment.');
  }
  if (code.trim() && !sql.trimEnd().endsWith(';')) statements += 1;
  return { code, statements };
}

export function checkReadOnlyPolicy(sql: string): PolicyResult {
  if (!sql.trim()) return { accepted: false, reason: 'Enter a query first.' };
  if (sql.length > MAX_QUERY_CHARS) return { accepted: false, reason: `Query exceeds ${MAX_QUERY_CHARS} characters.` };
  let scanned;
  try { scanned = codeOnly(sql); } catch (error) {
    return { accepted: false, reason: error instanceof Error ? error.message : 'Could not inspect SQL.' };
  }
  if (scanned.statements !== 1) return { accepted: false, reason: 'Exactly one statement is allowed.' };
  const normalized = scanned.code.toUpperCase();
  if (!/^\s*(SELECT|WITH)\b/.test(normalized)) {
    return { accepted: false, reason: 'Only SELECT queries and read-only CTEs are supported.' };
  }
  const prohibited = /\b(INSERT|UPDATE|DELETE|REPLACE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|ANALYZE|LOAD_EXTENSION)\b/;
  const match = normalized.match(prohibited);
  if (match) return { accepted: false, reason: `${match[1]} is not allowed in the sample-data playground.` };
  return { accepted: true };
}
