/**
 * Type definitions for sample queries
 */

export type QueryCategory = 'basic' | 'intermediate' | 'advanced' | 'business_intelligence';
export type QueryDifficulty = 'beginner' | 'intermediate' | 'advanced';

export interface SampleQuery {
  id: string;
  schemaId: string;
  category: QueryCategory;
  difficulty: QueryDifficulty;
  naturalLanguage: string;
  sql: string;
  description: string;
  explanation: string;
  tags: string[];
  contract?: MetricContract;
}

export interface MetricContract {
  metricId: string;
  version: string;
  supportedDecision: string;
  inputGrain: string;
  outputGrain: string;
  sources: string[];
  formula: string;
  unit: string;
  population: string;
  analysisDate?: string;
  limitations: string[];
  evidenceChecks: string[];
}
