import { useQuery, useMutation } from '@tanstack/react-query';
import { demoApi } from '@/lib/api';
import { toast } from 'react-hot-toast';

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

export const useGenerateSQL = () => {
  return useMutation({
    mutationFn: async ({ query, schemaContext }: { query: string; schemaContext?: string }) => {
      return await demoApi.generateSQL(query, schemaContext);
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success('SQL generated successfully!');
      }
    },
    onError: (error: any) => {
      if (error.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait a moment.');
      } else {
        toast.error('Failed to generate SQL. Please try again.');
      }
    },
  });
};

export const useMetrics = () => {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: demoApi.getMetrics,
    refetchInterval: 5000, // Refresh every 5 seconds
  });
};

export const useExecuteSandbox = () => {
  return useMutation({
    mutationFn: async (sql: string) => {
      return await demoApi.executeSandbox(sql);
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`Query executed! ${data.rows_affected} rows affected.`);
      }
    },
    onError: () => {
      toast.error('Failed to execute query in sandbox.');
    },
  });
};

export const useSchemaTemplates = () => {
  return useQuery({
    queryKey: ['schema-templates'],
    queryFn: demoApi.getSchemaTemplates,
  });
};

export const useSampleQueries = () => {
  return useQuery({
    queryKey: ['sample-queries'],
    queryFn: demoApi.getSampleQueries,
  });
};