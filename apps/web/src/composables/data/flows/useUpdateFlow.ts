import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {updateFlowApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

export function useUpdateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({id, patch}: { id: string; patch: Partial<Flow> }) => updateFlowApi(id, patch),

    onSuccess: async (updated: Flow) => {
      qc.setQueryData(qk.flows.detail(updated.id), updated);

      await qc.invalidateQueries({queryKey: qk.flows.base()});
      await qc.refetchQueries({queryKey: qk.flows.base(), type: 'active'});
    },
  });
}
