import { ecommerceQueries } from './ecommerce-queries';
import { saasQueries } from './saas-queries';
import { healthcareQueries } from './healthcare-queries';
import { financeQueries } from './finance-queries';
import { socialQueries } from './social-queries';
import type { SampleQuery } from './types';

export const allQueries: SampleQuery[] = [
  ...ecommerceQueries,
  ...saasQueries,
  ...healthcareQueries,
  ...financeQueries,
  ...socialQueries,
];

export const getQueriesBySchema = (schemaId: string): SampleQuery[] => {
  return allQueries.filter((query) => query.schemaId === schemaId);
};

export const getQueriesByCategory = (category: string): SampleQuery[] => {
  return allQueries.filter((query) => query.category === category);
};

export const getQueriesByDifficulty = (difficulty: string): SampleQuery[] => {
  return allQueries.filter((query) => query.difficulty === difficulty);
};

export const searchQueries = (searchTerm: string): SampleQuery[] => {
  const term = searchTerm.toLowerCase();
  return allQueries.filter(
    (query) =>
      query.naturalLanguage.toLowerCase().includes(term) ||
      query.description.toLowerCase().includes(term) ||
      query.tags.some((tag) => tag.toLowerCase().includes(term))
  );
};

export * from './types';
export {
  ecommerceQueries,
  saasQueries,
  healthcareQueries,
  financeQueries,
  socialQueries,
};
