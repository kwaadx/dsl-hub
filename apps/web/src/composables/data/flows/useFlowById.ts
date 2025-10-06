import {computed, type MaybeRef, unref} from 'vue';
import {useQuery} from '@tanstack/vue-query';
import {fetchFlowByIdApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

export function useFlowById(id: MaybeRef<string | null | undefined>) {
  const idStr = computed(() => String(unref(id) ?? ''));
  const enabled = computed(() => idStr.value.length > 0);
  const key = computed(() =>
    enabled.value ? qk.flows.detail(idStr.value) : qk.flows.detail('__off__')
  );

  return useQuery<Flow>({
    queryKey: key,
    queryFn: ({signal}) => fetchFlowByIdApi(idStr.value, signal),
    enabled,
    staleTime: 30_000,
    gcTime: 5 * 60_000,
  });
}
