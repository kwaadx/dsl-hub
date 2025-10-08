import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {deleteFlowApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';
import { retry404Safe } from '@/lib/retry';

export function useDeleteFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({id, signal}: { id: string; signal?: AbortSignal }) => deleteFlowApi(id, signal),
    retry: retry404Safe,

    onSuccess: async (_data, {id}) => {
      const listKey = qk.flows.list();
      const prevList = qc.getQueryData<Flow[] | undefined>(listKey) ?? [];
      const deleted = prevList.find(f => f.id === id);

      qc.removeQueries({queryKey: qk.flows.detail(id), exact: true});
      if (deleted?.slug) {
        qc.removeQueries({queryKey: qk.flows.detail(`slug:${deleted.slug}`), exact: true});
      }

      const next = prevList.filter(f => f.id !== id);
      qc.setQueryData(listKey, next);
    },
  });
}
