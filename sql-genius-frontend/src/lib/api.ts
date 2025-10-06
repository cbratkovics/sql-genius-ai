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

// Demo API endpoints using relative paths
export const demoApi = {
  generateSQL: async (query: string, schemaContext?: string) => {
    return post<{ sql: string; explanation: string }>('/v1/demo/sql-generate', {
      query,
      schema_context: schemaContext,
    }, withAuth());
  },

  getMetrics: async () => {
    return get('/v1/demo/metrics', withAuth());
  },

  executeSandbox: async (sql: string) => {
    return post('/v1/demo/execute-sandbox', { sql }, withAuth());
  },

  getSchemaTemplates: async () => {
    return get('/v1/demo/schema-templates', withAuth());
  },

  getSampleQueries: async () => {
    return get('/v1/demo/sample-queries', withAuth());
  },
};