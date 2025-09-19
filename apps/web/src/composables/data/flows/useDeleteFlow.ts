import { useMutation, useQueryClient } from '@tanstack/vue-query';
import { deleteFlowApi } from '@/services/flow';
import { qk } from '../queryKeys';

export function useDeleteFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteFlowApi(id),

    onSuccess: (_void, id) => {
      qc.invalidateQueries({ queryKey: qk.flows.list() });
      qc.removeQueries({ queryKey: qk.flows.detail(id) });
    },
  });
}
