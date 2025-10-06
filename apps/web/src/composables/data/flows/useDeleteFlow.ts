import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {deleteFlowApi} from '@/services/flow';
import {qk} from '../queryKeys';

export function useDeleteFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({id, signal}: { id: string; signal?: AbortSignal }) => deleteFlowApi(id, signal),

    onSuccess: async (_data, {id}) => {
      qc.removeQueries({queryKey: qk.flows.detail(id), exact: true});

      await qc.invalidateQueries({queryKey: qk.flows.base()});
      await qc.refetchQueries({queryKey: qk.flows.base(), type: 'active'});
    },
  });
}
