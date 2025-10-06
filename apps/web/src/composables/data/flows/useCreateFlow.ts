import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {createFlowApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

export function useCreateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (payload: { name: string; slug?: string }) => createFlowApi(payload),

    onSuccess: async (created: Flow) => {
      qc.setQueryData(qk.flows.detail(created.id), created);

      await qc.invalidateQueries({queryKey: qk.flows.base()});
      await qc.refetchQueries({queryKey: qk.flows.base(), type: 'active'});
    },
  });
}
