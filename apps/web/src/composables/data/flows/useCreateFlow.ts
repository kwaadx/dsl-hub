import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { createFlowApi, type Flow } from '@/services/flow';
import { qk } from '../queryKeys';

export function useCreateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: { name: string }) => createFlowApi(payload),

    onSuccess: (created: Flow) => {
      qc.invalidateQueries({ queryKey: qk.flows.list() });
      qc.setQueryData(qk.flows.detail(created.id), created);
    },
  });
}
