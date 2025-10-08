import {computed, type MaybeRef, unref} from 'vue';
import {useQuery} from '@tanstack/vue-query';
import {fetchThreadsForFlowApi, type Thread} from '@/services/thread';
import {qk} from '../queryKeys';

export function useThreadsForFlow(flowId: MaybeRef<string | null | undefined>) {
  const idStr = computed(() => String(unref(flowId) ?? ''));
  const enabled = computed(() => idStr.value.length > 0);
  const key = computed(() => enabled.value ? qk.threads.list(idStr.value) : qk.threads.list('__off__'));

  return useQuery<Thread[]>({
    queryKey: key,
    queryFn: ({signal}) => fetchThreadsForFlowApi(idStr.value, signal),
    enabled,
    staleTime: 10_000,
    gcTime: 5 * 60_000,
  });
}
