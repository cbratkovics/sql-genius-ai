import type { SampleQuery } from '@/data/queries/types';
import type { SchemaTemplate } from '@/data/schemas/types';

export interface LocalGenerationResult {
  sql: string;
  explanation: string;
  assumptions: string[];
  match: 'curated-intent' | 'schema-fallback';
  confidence: number;
}

const STOP_WORDS = new Set([
  'a', 'all', 'and', 'are', 'by', 'calculate', 'each', 'find', 'for', 'from',
  'get', 'give', 'in', 'list', 'me', 'of', 'per', 'please', 'show', 'the', 'to', 'with',
]);

const normalize = (value: string) => value
  .toLowerCase()
  .replace(/[^a-z0-9_]+/g, ' ')
  .trim();

const stem = (word: string) => {
  if (word.endsWith('ies') && word.length > 4) return `${word.slice(0, -3)}y`;
  if (word.endsWith('ses') && word.length > 4) return word.slice(0, -2);
  if (word.endsWith('s') && !word.endsWith('ss') && word.length > 3) return word.slice(0, -1);
  return word;
};

const tokens = (value: string) => new Set(
  normalize(value).split(/\s+/).filter(Boolean).map(stem).filter((word) => !STOP_WORDS.has(word)),
);

function similarity(question: string, sample: SampleQuery): number {
  const wanted = tokens(question);
  const candidate = tokens(`${sample.naturalLanguage} ${sample.description} ${sample.tags.join(' ')}`);
  if (!wanted.size) return 0;
  let overlap = 0;
  for (const word of wanted) if (candidate.has(word)) overlap += 1;
  return overlap / wanted.size;
}

function quoteIdentifier(identifier: string): string {
  return `"${identifier.replaceAll('"', '""')}"`;
}

function bestTable(question: string, schema: SchemaTemplate) {
  const questionTokens = tokens(question);
  return schema.tables
    .map((table, index) => {
      const tableTokens = tokens(table.name.replaceAll('_', ' '));
      const columnMatches = table.columns.filter((column) => {
        const columnTokens = tokens(column.name.replaceAll('_', ' '));
        return [...columnTokens].some((word) => questionTokens.has(word));
      }).length;
      const tableMatches = [...tableTokens].filter((word) => questionTokens.has(word)).length;
      return { table, index, score: tableMatches * 4 + columnMatches };
    })
    .sort((a, b) => b.score - a.score || a.index - b.index)[0];
}

/**
 * Generates useful, read-only SQLite without a network request. Reviewed examples are
 * treated as an intent library; unknown wording falls back to the most relevant table.
 */
export function generateLocalSQL(
  question: string,
  schema: SchemaTemplate,
  samples: SampleQuery[],
): LocalGenerationResult {
  const normalizedQuestion = normalize(question);
  const ranked = samples
    .map((sample, index) => ({ sample, index, score: similarity(question, sample) }))
    .sort((a, b) => b.score - a.score || a.index - b.index);
  const exact = ranked.find(({ sample }) => normalize(sample.naturalLanguage) === normalizedQuestion);
  const best = exact ?? ranked[0];

  // Multiple meaningful matching words are deliberately required to avoid confidently
  // returning an unrelated example for short or novel requests.
  if (best && (exact || best.score >= 0.66)) {
    return {
      sql: best.sample.sql,
      explanation: `Matched your request to the reviewed “${best.sample.description}” query for this schema.`,
      assumptions: ['Results use the bundled sample dataset and SQLite semantics.'],
      match: 'curated-intent',
      confidence: exact ? 1 : best.score,
    };
  }

  const selected = bestTable(question, schema);
  const tableName = quoteIdentifier(selected.table.name);
  const wantsCount = /\b(how many|count|number of)\b/i.test(question);
  const sql = wantsCount
    ? `SELECT COUNT(*) AS "row_count"\nFROM ${tableName};`
    : `SELECT *\nFROM ${tableName}\nLIMIT 100;`;

  return {
    sql,
    explanation: wantsCount
      ? `Counts rows in ${selected.table.name}, the table that best matches your request.`
      : `Shows a safe preview from ${selected.table.name}, the table that best matches your request.`,
    assumptions: [
      'The wording did not closely match a reviewed advanced query, so a conservative read-only query was generated.',
      'Refine the request or edit the SQL when you need specific filters, joins, or business definitions.',
    ],
    match: 'schema-fallback',
    confidence: selected.score > 0 ? 0.6 : 0.35,
  };
}
