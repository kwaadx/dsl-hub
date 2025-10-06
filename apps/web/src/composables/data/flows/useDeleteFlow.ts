import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {type Flow, deleteFlowApi} from '@/services/flow';
import {qk} from '../queryKeys';

export function useDeleteFlow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({id, signal}: { id: string; signal?: AbortSignal }) => deleteFlowApi(id, signal),
    onSuccess: async (_data, { id: flowId }) => {
      qc.getQueriesData<Flow[]>({ queryKey: qk.flows.list() })
        .forEach(([key, data]) => {
          if (!data) return;
          qc.setQueryData<Flow[]>(key, data.filter(f => f.id !== flowId));
        });

      qc.removeQueries({ queryKey: qk.flows.detail(flowId), exact: true });
      await qc.invalidateQueries({ queryKey: qk.flows.base() });
    }
  });
}
