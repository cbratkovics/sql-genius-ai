import type { SampleQuery } from '@/data/queries/types';
import type { SchemaTemplate } from '@/data/schemas/types';

interface GenerationBase { explanation: string; assumptions: string[] }
export type LocalGenerationResult =
  | (GenerationBase & { kind: 'supported'; sql: string; sampleId: string; retrievalScore?: number })
  | (GenerationBase & { kind: 'clarification'; question: string; options: ClarificationOption[] })
  | (GenerationBase & { kind: 'unsupported'; missing: string[]; exploration?: { label: 'Explore available data'; sql: string } })
  | (GenerationBase & { kind: 'exploration'; label: 'Explore available data'; sql: string });

export interface ClarificationOption { id: 'observed-value' | 'completed-frequency'; label: string; metric: string; population: string; period: string }
export const BEST_CUSTOMER_OPTIONS: ClarificationOption[] = [
  { id: 'observed-value', label: 'Observed completed-order value', metric: 'Sum of order-header total_amount', population: "Orders with status = 'delivered'", period: '2024-06-01 through 2024-06-15' },
  { id: 'completed-frequency', label: 'Completed-order frequency', metric: 'Count of delivered order headers', population: "Orders with status = 'delivered'", period: '2024-06-01 through 2024-06-15' },
];

const STOP_WORDS = new Set(['a','all','and','are','by','calculate','each','find','for','from','get','give','in','list','me','of','per','please','show','the','to','with']);
const normalize = (value: string) => value.toLowerCase().replace(/[^a-z0-9_$]+/g, ' ').trim();
const stem = (word: string) => word.endsWith('ies') && word.length > 4 ? `${word.slice(0,-3)}y` : word.endsWith('s') && !word.endsWith('ss') && word.length > 3 ? word.slice(0,-1) : word;
const tokens = (value: string) => new Set(normalize(value).split(/\s+/).filter(Boolean).map(stem).filter(word => !STOP_WORDS.has(word)));
function similarity(question: string, sample: SampleQuery) { const wanted=tokens(question); const candidate=tokens(`${sample.naturalLanguage} ${sample.description} ${sample.tags.join(' ')}`); if(!wanted.size)return 0; return [...wanted].filter(word=>candidate.has(word)).length/wanted.size; }
const quoteIdentifier = (identifier: string) => `"${identifier.replaceAll('"','""')}"`;
function bestTable(question: string, schema: SchemaTemplate) { const wanted=tokens(question); return schema.tables.map((table,index)=>({table,index,score:[...tokens(table.name.replaceAll('_',' '))].filter(w=>wanted.has(w)).length*4+table.columns.filter(c=>[...tokens(c.name.replaceAll('_',' '))].some(w=>wanted.has(w))).length})).sort((a,b)=>b.score-a.score||a.index-b.index)[0]; }

export function resolveBestCustomers(optionId: ClarificationOption['id']): LocalGenerationResult {
  const option = BEST_CUSTOMER_OPTIONS.find(item => item.id === optionId)!;
  const aggregate = optionId === 'observed-value' ? 'ROUND(SUM(o.total_amount), 2) AS metric_value' : 'COUNT(o.order_id) AS metric_value';
  return { kind:'supported', sampleId:`best-customers-${optionId}`, sql:`SELECT c.customer_id, c.first_name, c.last_name, ${aggregate}\nFROM customers c\nJOIN orders o ON o.customer_id = c.customer_id\nWHERE o.status = 'delivered'\n  AND o.order_date >= '2024-06-01' AND o.order_date < '2024-06-16'\nGROUP BY c.customer_id, c.first_name, c.last_name\nORDER BY metric_value DESC, c.customer_id ASC;`, explanation:`${option.label}: ${option.metric}, for ${option.population}, ${option.period}.`, assumptions:['Order-header totals are used once per order to avoid child-row fan-out.','The customer total_spent snapshot is a different scope and is not substituted.'] };
}

export function generateLocalSQL(question: string, schema: SchemaTemplate, samples: SampleQuery[]): LocalGenerationResult {
  const normalized=normalize(question);
  if (!normalized) return {kind:'unsupported', explanation:'Enter a question before choosing SQL.', assumptions:[], missing:['A non-empty business question']};
  if (!schema.tables.length) return {kind:'unsupported', explanation:'This schema has no inspectable tables.', assumptions:[], missing:['A valid loaded schema']};
  if (schema.id==='ecommerce' && /\bbest customers?\b/.test(normalized)) return {kind:'clarification', question:'How should “best” be defined?', options:BEST_CUSTOMER_OPTIONS, explanation:'The ranking changes with the metric and eligible population. Choose a supported definition; both use the fixture period.', assumptions:[]};
  const unsupported:string[]=[];
  if (/\bprofit(ability)?\b/.test(normalized)) unsupported.push('Product cost data is required to calculate profit.');
  if (/\b(predicted?|forecast)\b.*\b(lifetime|churn|growth)\b|\bcaus(e|al|ality)\b/.test(normalized)) unsupported.push('A validated predictive or causal method and suitable history are required.');
  if (unsupported.length) { const selected=bestTable(question,schema); return {kind:'unsupported', explanation:'The requested conclusion is not supported by this synthetic fixture.', assumptions:[], missing:unsupported, exploration:selected?{label:'Explore available data',sql:`SELECT *\nFROM ${quoteIdentifier(selected.table.name)}\nLIMIT 100;`}:undefined}; }
  const ranked=samples.map((sample,index)=>({sample,index,score:similarity(question,sample)})).sort((a,b)=>b.score-a.score||a.index-b.index);
  const exact=ranked.find(({sample})=>normalize(sample.naturalLanguage)===normalized); const best=exact??ranked[0];
  const constraints=/\b(not|without|before|after|between|over|under|more than|less than|ascending|oldest|excluding?|only)\b|\b\d{4}-\d{2}-\d{2}\b|\$\d+/.test(normalized);
  const tied=!exact && ranked.length>1 && ranked[0].score===ranked[1].score && ranked[0].score>0;
  if (best && (exact || (best.score>=0.66 && !constraints && !tied))) return {kind:'supported',sql:best.sample.sql,sampleId:best.sample.id,retrievalScore:best.score,explanation:`Matched the reviewed “${best.sample.description}” intent.`,assumptions:['Results use the selected bundled fixture and SQLite semantics.']};
  if (tied || constraints) return {kind:'clarification',question:'Which reviewed definition and constraints should apply?',options:[],explanation:'The request contains an unsupported constraint or maps equally to multiple templates, so no answer SQL was selected.',assumptions:[]};
  const selected=bestTable(question,schema);
  if (!selected) return {kind:'unsupported',explanation:'No matching sample or table is available.',assumptions:[],missing:['A table relevant to the request']};
  const wantsCount=/\b(how many|count|number of)\b/i.test(question); const table=quoteIdentifier(selected.table.name);
  return {kind:'exploration',label:'Explore available data',sql:wantsCount?`SELECT COUNT(*) AS "row_count"\nFROM ${table};`:`SELECT *\nFROM ${table}\nLIMIT 100;`,explanation:'This exploratory query does not answer the original business question.',assumptions:['Add a supported definition and filters before treating this as an answer.']};
}
