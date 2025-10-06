import { ecommerceSchema } from './ecommerce';
import { saasSchema } from './saas';
import { healthcareSchema } from './healthcare';
import { financeSchema } from './finance';
import { socialSchema } from './social';
import type { SchemaTemplate } from './types';

export const schemas: SchemaTemplate[] = [
  ecommerceSchema,
  saasSchema,
  healthcareSchema,
  financeSchema,
  socialSchema,
];

export const getSchemaById = (id: string): SchemaTemplate | undefined => {
  return schemas.find((schema) => schema.id === id);
};

export const getSchemasByCategory = (category: string): SchemaTemplate[] => {
  return schemas.filter((schema) => schema.category === category);
};

export const getSchemasByDifficulty = (difficulty: string): SchemaTemplate[] => {
  return schemas.filter((schema) => schema.difficulty === difficulty);
};

export * from './types';
export { ecommerceSchema, saasSchema, healthcareSchema, financeSchema, socialSchema };
