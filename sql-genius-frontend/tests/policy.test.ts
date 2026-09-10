import test from 'node:test';
import assert from 'node:assert/strict';
import { checkReadOnlyPolicy } from '../src/lib/sql/policy.ts';
import { rowsToCsv } from '../src/lib/csv.ts';

test('accepts supported selects, CTE aliases, and keywords in strings/comments', () => {
  for (const sql of [
    'SELECT 0 AS zero',
    "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
    "SELECT 'DROP TABLE orders; -- text' AS note /* DELETE is text here */",
  ]) assert.equal(checkReadOnlyPolicy(sql).accepted, true, sql);
});

test('rejects multiple statements and side-effecting SQLite operations', () => {
  for (const sql of [
    'SELECT 1; SELECT 2',
    'DELETE FROM orders',
    'WITH changed AS (DELETE FROM orders RETURNING *) SELECT * FROM changed',
    "ATTACH DATABASE 'other.db' AS other",
    'PRAGMA writable_schema=ON',
    "SELECT load_extension('x')",
  ]) assert.equal(checkReadOnlyPolicy(sql).accepted, false, sql);
});

test('CSV quotes special values, preserves zero/null, and protects text formulas', () => {
  assert.equal(
    rowsToCsv(['name', 'value'], [['a,b', 0], ['a"b', null], ['line\nbreak', '=2+2'], ['negative', -2]]),
    '"name","value"\r\n"a,b","0"\r\n"a""b",\r\n"line\nbreak","\'=2+2"\r\n"negative","-2"',
  );
});
