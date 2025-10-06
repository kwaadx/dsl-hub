import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {deleteFlowApi} from '@/services/flow';
import {qk} from '../queryKeys';

export function useDeleteFlow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({id, signal}: { id: string; signal?: AbortSignal }) => deleteFlowApi(id, signal),
    onSuccess: async (_data, variables) => {
      await qc.invalidateQueries({ queryKey: qk.flows.base() });
      qc.removeQueries({ queryKey: qk.flows.detail(variables.id) });
    },
  });
}
