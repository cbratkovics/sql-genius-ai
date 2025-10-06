export async function post<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    body: body ? JSON.stringify(body) : undefined,
    ...init
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

// Helper to add auth token
export function withAuth(init?: RequestInit): RequestInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  };
}

// Type definitions
export interface SQLGenerationResult {
  success: boolean;
  sql: string;
  explanation: string;
  confidence_score: number;
  performance: {
    generation_time_ms: number;
    tokens_used: number;
    model: string;
    cached: boolean;
  };
  security: {
    injection_safe: boolean;
    validated: boolean;
    sandbox_tested: boolean;
  };
}

export interface SandboxExecuteResult {
  success: boolean;
  sample_results: Array<Record<string, unknown>>;
  rows_affected: number;
  columns: string[];
  execution_time_ms: number;
}

export interface Schema {
  name: string;
  description: string;
  tables: Array<{
    name: string;
    columns: Array<{
      name: string;
      type: string;
    }>;
  }>;
}

export interface SampleQuery {
  title: string;
  query: string;
  description: string;
  category: string;
}

// Demo API endpoints using relative paths
export const demoApi = {
  generateSQL: async (query: string, schemaContext?: string): Promise<SQLGenerationResult> => {
    return post<SQLGenerationResult>('/v1/demo/sql-generate', {
      query,
      schema_context: schemaContext,
    }, withAuth());
  },

  getMetrics: async () => {
    return get('/v1/demo/metrics', withAuth());
  },

  executeSandbox: async (sql: string): Promise<SandboxExecuteResult> => {
    return post<SandboxExecuteResult>('/v1/demo/execute-sandbox', { sql }, withAuth());
  },

  getSchemaTemplates: async (): Promise<Schema[]> => {
    return get<Schema[]>('/v1/demo/schema-templates', withAuth());
  },

  getSampleQueries: async (): Promise<SampleQuery[]> => {
    return get<SampleQuery[]>('/v1/demo/sample-queries', withAuth());
  },
};