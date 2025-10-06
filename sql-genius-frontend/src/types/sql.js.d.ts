declare module 'sql.js' {
  export interface Database {
    run(sql: string): void;
    exec(sql: string): QueryExecResult[];
    prepare(sql: string): Statement;
    close(): void;
  }

  export interface QueryExecResult {
    columns: string[];
    values: unknown[][];
  }

  export interface Statement {
    bind(values?: unknown[]): boolean;
    step(): boolean;
    getAsObject(): Record<string, unknown>;
    get(): unknown[];
    run(values?: unknown[]): void;
    free(): void;
  }

  export interface Config {
    locateFile?: (file: string) => string;
  }

  export interface SqlJsStatic {
    Database: new () => Database;
  }

  export default function initSqlJs(config?: Config): Promise<SqlJsStatic>;
}
