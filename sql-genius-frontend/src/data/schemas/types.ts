/**
 * Type definitions for schema templates
 */

export type SchemaCategory = 'ecommerce' | 'saas' | 'healthcare' | 'finance' | 'social';
export type SchemaDifficulty = 'beginner' | 'intermediate' | 'advanced';

export interface Column {
  name: string;
  type: string;
  nullable?: boolean;
  primaryKey?: boolean;
  foreignKey?: {
    table: string;
    column: string;
  };
}

export interface Table {
  name: string;
  columns: Column[];
}

export interface Relationship {
  from: { table: string; column: string };
  to: { table: string; column: string };
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
}

export interface SchemaTemplate {
  id: string;
  name: string;
  description: string;
  category: SchemaCategory;
  difficulty: SchemaDifficulty;
  tables: Table[];
  sampleData: Record<string, Record<string, unknown>[]>;
  relationships: Relationship[];
  ddl: string;
  icon: string;
}
