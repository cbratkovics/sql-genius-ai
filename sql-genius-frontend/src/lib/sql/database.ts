import type { SchemaTemplate } from '@/data/schemas';

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
        locateFile: (file: string) => `https://sql.js.org/dist/${file}`,
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
  }> {
    if (!this.db) {
      throw new Error('No database loaded. Please select a schema first.');
    }

    try {
      const results = this.db.exec(sql);

      if (results.length === 0) {
        return { columns: [], values: [], rowCount: 0 };
      }

      const result = results[0];
      return {
        columns: result.columns,
        values: result.values,
        rowCount: result.values.length,
      };
    } catch (error) {
      console.error('Query execution error:', error);
      throw new Error(`SQL Error: ${error instanceof Error ? error.message : String(error)}`);
    }
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
