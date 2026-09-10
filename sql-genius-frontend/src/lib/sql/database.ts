import type { SchemaTemplate } from '@/data/schemas';
import { checkReadOnlyPolicy } from './policy';

// Type definitions for sql.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Database = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type InitSqlJs = any;

/**
 * SQL.js Database Manager
 * Handles in-browser SQLite database initialization and query execution
 */
export class SQLDatabase {
  private db: Database | null = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private SQL: any = null;
  private currentSchema: string | null = null;

  /**
   * Initialize SQL.js library
   * Must be called before any database operations
   */
  async initialize(): Promise<void> {
    if (this.SQL) return; // Already initialized

    try {
      // Dynamic import to avoid server-side issues
      const initSqlJs: InitSqlJs = (await import('sql.js')).default;
      this.SQL = await initSqlJs({
        locateFile: (file: string) => `/${file}`,
      });
    } catch (error) {
      console.error('Failed to initialize SQL.js:', error);
      throw new Error('Could not initialize SQL engine');
    }
  }

  /**
   * Load a schema template into the database
   * Drops existing tables and creates new schema
   */
  async loadSchema(schema: SchemaTemplate): Promise<void> {
    if (!this.SQL) {
      await this.initialize();
    }

    try {
      // Create new database (or reset existing one)
      if (this.db) {
        this.db.close();
      }
      this.db = new this.SQL.Database();

      // Execute DDL to create tables
      this.db.exec(schema.ddl);

      // Insert sample data for each table
      for (const [tableName, rows] of Object.entries(schema.sampleData)) {
        if (rows.length === 0) continue;

        // Get column names from first row
        const columns = Object.keys(rows[0]);
        const placeholders = columns.map(() => '?').join(', ');
        const insertSQL = `INSERT INTO ${tableName} (${columns.join(', ')}) VALUES (${placeholders})`;

        const stmt = this.db.prepare(insertSQL);
        for (const row of rows) {
          const values = columns.map((col) => row[col]);
          stmt.run(values);
        }
        stmt.free();
      }

      this.currentSchema = schema.id;
      console.log(`Schema "${schema.name}" loaded successfully`);
    } catch (error) {
      console.error('Failed to load schema:', error);
      throw new Error(`Could not load schema: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Execute a SQL query and return results
   */
  async executeQuery(sql: string): Promise<{
    columns: string[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    values: any[][];
    rowCount: number;
    truncated: boolean;
  }> {
    if (!this.db) {
      throw new Error('No database loaded. Please select a schema first.');
    }

    const policy = checkReadOnlyPolicy(sql);
    if (!policy.accepted) throw new Error(`Query blocked: ${policy.reason}`);
    const MAX_ROWS = 500;
    const MAX_RESULT_BYTES = 1_000_000;
    let statement: ReturnType<Database['prepare']> | null = null;
    try {
      // Preparation delegates SQLite syntax/name checking to the actual execution engine.
      statement = this.db.prepare(sql);
      const columns = statement.getColumnNames();
      const values: unknown[][] = [];
      let bytes = 0;
      while (values.length < MAX_ROWS && statement.step()) {
        const row = statement.get();
        bytes += row.reduce((total: number, value: unknown) => total + String(value ?? '').length, 0);
        if (bytes > MAX_RESULT_BYTES) throw new Error('Result preview exceeds the 1 MB collection limit.');
        values.push(row);
      }
      const truncated = values.length === MAX_ROWS && statement.step();
      return {
        columns,
        values,
        rowCount: values.length,
        truncated,
      };
    } catch (error) {
      console.error('Query execution error:', error);
      throw new Error(`SQL Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally { statement?.free(); }
  }

  /**
   * Execute a query and return results as objects
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async executeQueryAsObjects(sql: string): Promise<Record<string, any>[]> {
    const { columns, values } = await this.executeQuery(sql);

    return values.map((row) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const obj: Record<string, any> = {};
      columns.forEach((col, idx) => {
        obj[col] = row[idx];
      });
      return obj;
    });
  }

  /**
   * Get current schema ID
   */
  getCurrentSchema(): string | null {
    return this.currentSchema;
  }

  /**
   * Check if database is ready
   */
  isReady(): boolean {
    return this.db !== null;
  }

  /**
   * Get table names in current database
   */
  getTableNames(): string[] {
    if (!this.db) return [];

    try {
      const result = this.db.exec(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
      );

      if (result.length === 0) return [];

      return result[0].values.map((row: unknown[]) => row[0] as string);
    } catch (error) {
      console.error('Error getting table names:', error);
      return [];
    }
  }

  /**
   * Get table schema information
   */
  getTableSchema(tableName: string): Array<{ name: string; type: string }> {
    if (!this.db) return [];

    try {
      const result = this.db.exec(`PRAGMA table_info(${tableName})`);

      if (result.length === 0) return [];

      return result[0].values.map((row: unknown[]) => ({
        name: row[1] as string,
        type: row[2] as string,
      }));
    } catch (error) {
      console.error(`Error getting schema for table ${tableName}:`, error);
      return [];
    }
  }

  /**
   * Clean up database resources
   */
  close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      this.currentSchema = null;
    }
  }
}

// Singleton instance
let dbInstance: SQLDatabase | null = null;

export function getDatabase(): SQLDatabase {
  if (!dbInstance) {
    dbInstance = new SQLDatabase();
  }
  return dbInstance;
}
