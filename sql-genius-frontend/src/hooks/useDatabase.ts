import { useState, useEffect, useCallback } from 'react';
import { getDatabase } from '@/lib/sql/database';
import type { SchemaTemplate } from '@/data/schemas';
import { toast } from 'react-hot-toast';

/**
 * Hook for managing SQL.js database instance
 */
export function useDatabase() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentSchema, setCurrentSchema] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const db = getDatabase();

  // Initialize database on mount
  useEffect(() => {
    const init = async () => {
      try {
        setIsLoading(true);
        await db.initialize();
        setIsInitialized(true);
        setError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to initialize database';
        setError(message);
        toast.error(message);
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  const loadSchema = useCallback(
    async (schema: SchemaTemplate) => {
      try {
        setIsLoading(true);
        setError(null);
        await db.loadSchema(schema);
        setCurrentSchema(schema.id);
        toast.success(`Schema "${schema.name}" loaded successfully`);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load schema';
        setError(message);
        toast.error(message);
      } finally {
        setIsLoading(false);
      }
    },
    [db]
  );

  const executeQuery = useCallback(
    async (sql: string) => {
      try {
        return await db.executeQuery(sql);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Query execution failed';
        throw new Error(message);
      }
    },
    [db]
  );

  const executeQueryAsObjects = useCallback(
    async (sql: string) => {
      try {
        return await db.executeQueryAsObjects(sql);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Query execution failed';
        throw new Error(message);
      }
    },
    [db]
  );

  return {
    isInitialized,
    isLoading,
    currentSchema,
    error,
    loadSchema,
    executeQuery,
    executeQueryAsObjects,
    getTableNames: () => db.getTableNames(),
    getTableSchema: (tableName: string) => db.getTableSchema(tableName),
    isReady: () => db.isReady(),
  };
}

/**
 * Hook for executing SQL queries with loading states
 */
export function useSQLQuery() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [results, setResults] = useState<{
    columns: string[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    values: any[][];
    rowCount: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const db = getDatabase();

  const execute = useCallback(
    async (sql: string) => {
      try {
        setIsExecuting(true);
        setError(null);
        const result = await db.executeQuery(sql);
        setResults(result);
        toast.success(`Query executed successfully. ${result.rowCount} rows returned.`);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Query execution failed';
        setError(message);
        toast.error(message);
        throw err;
      } finally {
        setIsExecuting(false);
      }
    },
    [db]
  );

  const reset = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    execute,
    reset,
    isExecuting,
    results,
    error,
  };
}
