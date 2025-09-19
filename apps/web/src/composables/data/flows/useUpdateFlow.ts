import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { updateFlowApi, type Flow } from '@/services/flow';
import { qk } from '../queryKeys';

export function useUpdateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<Flow> }) =>
      updateFlowApi(id, patch),

    onSuccess: (updated: Flow) => {
      qc.invalidateQueries({ queryKey: qk.flows.list() });
      qc.setQueryData(qk.flows.detail(updated.id), updated);
    },
  });
}
