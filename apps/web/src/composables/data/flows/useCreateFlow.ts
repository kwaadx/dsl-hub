import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {createFlowApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

export function useCreateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: { name: string; slug?: string }) => createFlowApi(payload),

    onSuccess: async (created: Flow) => {
      qc.setQueryData(qk.flows.detail(created.id), created);
      if (created.slug) {
        qc.setQueryData(qk.flows.detail(`slug:${created.slug}`), created);
      }

      const listKey = qk.flows.list();
      const prev = qc.getQueryData<Flow[] | undefined>(listKey) ?? [];
      const exists = prev.some(f => f.id === created.id);
      const next = exists ? prev.map(f => (f.id === created.id ? created : f)) : [...prev, created];
      qc.setQueryData(listKey, next);
    },
  });
}
