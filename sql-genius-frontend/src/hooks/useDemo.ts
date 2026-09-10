import { useMutation } from '@tanstack/react-query';
import { demoApi, type GenerationSchema } from '@/lib/api';
import { toast } from 'react-hot-toast';

export const useGenerateSQL = () => {
  return useMutation({
    mutationFn: async ({ query, schema }: { query: string; schema: GenerationSchema }) => {
      return await demoApi.generateSQL(query, schema);
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success('SQL generated. Review it before running.');
      }
    },
    onError: (error: unknown) => {
      toast.error(error instanceof Error ? error.message : 'SQL generation failed.');
    },
  });
};
