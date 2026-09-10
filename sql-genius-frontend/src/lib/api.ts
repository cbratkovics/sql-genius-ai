export async function post<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
    ...init,
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `API request failed (${res.status}).`);
  }
  return res.json() as Promise<T>;
}

export interface SQLGenerationResult {
  success: true;
  sql: string;
  explanation: string;
  assumptions: string[];
  metadata: {
    source: 'provider';
    provider: string;
    model: string;
    dialect: 'sqlite';
    schema_id: string;
    response_parsed: boolean;
    policy_status: 'not_checked';
    execution_status: 'not_run';
    provider_round_trip_ms: number;
    input_tokens: number | null;
    output_tokens: number | null;
  };
}

export interface GenerationSchema {
  id: string;
  dialect: 'sqlite';
  tables: Array<{ name: string; columns: Array<{ name: string; type: string }> }>;
  relationships: Array<{ source: string; target: string }>;
}

export const demoApi = {
  generateSQL: (query: string, schema: GenerationSchema): Promise<SQLGenerationResult> =>
    post<SQLGenerationResult>('/v1/demo/sql-generate', { query, schema }),
};
