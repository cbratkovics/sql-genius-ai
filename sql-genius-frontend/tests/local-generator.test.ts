import test from 'node:test';
import assert from 'node:assert/strict';
import { generateLocalSQL } from '../src/lib/sql/local-generator.ts';
import type { SchemaTemplate } from '../src/data/schemas/types.ts';
import type { SampleQuery } from '../src/data/queries/types.ts';

const schema = {
  id: 'test',
  name: 'Test',
  description: 'Test data',
  category: 'saas',
  difficulty: 'beginner',
  icon: 'T',
  ddl: '',
  sampleData: {},
  relationships: [],
  tables: [
    { name: 'organizations', columns: [{ name: 'org_id', type: 'INTEGER' }, { name: 'name', type: 'TEXT' }] },
    { name: 'usage_events', columns: [{ name: 'event_id', type: 'INTEGER' }] },
  ],
} satisfies SchemaTemplate;

const samples = [{
  id: 'test-1', schemaId: 'test', category: 'basic', difficulty: 'beginner',
  naturalLanguage: 'Show all organizations', sql: 'SELECT * FROM organizations;',
  description: 'List organizations', explanation: 'List all', tags: ['organizations'],
}] satisfies SampleQuery[];

test('returns reviewed SQL for exact and closely matching intents', () => {
  assert.equal(generateLocalSQL('Show all organizations', schema, samples).sql, 'SELECT * FROM organizations;');
  assert.equal(generateLocalSQL('list organizations', schema, samples).match, 'curated-intent');
});

test('creates conservative schema-aware fallback SQL for novel requests', () => {
  const preview = generateLocalSQL('inspect usage events carefully', schema, samples);
  assert.equal(preview.sql, 'SELECT *\nFROM "usage_events"\nLIMIT 100;');
  assert.equal(preview.match, 'schema-fallback');

  const count = generateLocalSQL('how many usage events exist?', schema, samples);
  assert.equal(count.sql, 'SELECT COUNT(*) AS "row_count"\nFROM "usage_events";');
});
