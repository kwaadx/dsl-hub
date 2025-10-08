import { computed, type MaybeRef, unref } from 'vue'
import { useQuery, keepPreviousData } from '@tanstack/vue-query'
import { fetchFlowByIdApi, type Flow } from '@/services/flow'
import { qk } from '../queryKeys'
import { retry404Safe } from '@/lib/retry'

export function useFlowById(id: MaybeRef<string | null | undefined>) {
  const idStr = computed(() => String(unref(id) ?? '').trim())
  const enabled = computed(() => idStr.value.length > 0)
  const key = computed(() => qk.flows.detail(idStr.value))

  return useQuery<Flow>({
    queryKey: key,
    enabled,
    queryFn: ({ signal }) => fetchFlowByIdApi(idStr.value, signal),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    retry: retry404Safe,
    select: (data) => Object.freeze({ ...data }),
  })
}
