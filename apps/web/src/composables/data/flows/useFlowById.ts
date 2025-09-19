import { computed, unref, type MaybeRef } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { fetchFlowByIdApi, type Flow } from '@/services/flow';
import { qk } from '../queryKeys';

export function useFlowById(id: MaybeRef<string | null | undefined>) {
  const enabled = computed(() => {
    const v = unref(id);
    return !!v && v.length > 0;
  });

  return useQuery<Flow>({
    queryKey: computed(() => qk.flows.detail(String(unref(id) ?? ''))),
    queryFn: ({ signal }) => fetchFlowByIdApi(String(unref(id)), signal),
    enabled,
    staleTime: 60_000,
  });
}
