import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {updateFlowApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

export function useUpdateFlow() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({id, patch}: { id: string; patch: Partial<Flow> }) => updateFlowApi(id, patch),

    onSuccess: async (updated: Flow) => {
      const listKey = qk.flows.list();
      const prevList = qc.getQueryData<Flow[] | undefined>(listKey) ?? [];
      const prevItem = prevList.find(f => f.id === updated.id);
      const oldSlug = prevItem?.slug;

      qc.setQueryData(qk.flows.detail(updated.id), updated);
      if (oldSlug && oldSlug !== updated.slug) {
        qc.removeQueries({queryKey: qk.flows.detail(`slug:${oldSlug}`), exact: true});
      }
      if (updated.slug) {
        qc.setQueryData(qk.flows.detail(`slug:${updated.slug}`), updated);
      }

      const next = prevList.length
        ? prevList.map(f => (f.id === updated.id ? {...f, ...updated} : f))
        : [updated];
      qc.setQueryData(listKey, next);
    },
  });
}
