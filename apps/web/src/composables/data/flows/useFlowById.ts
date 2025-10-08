import { computed, type MaybeRef, unref } from 'vue'
import { useQuery, keepPreviousData } from '@tanstack/vue-query'
import { fetchFlowByIdApi, type Flow } from '@/services/flow'
import { qk } from '../queryKeys'

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
    retry: (failureCount, error: any) => {
      const status = error?.status ?? error?.response?.status
      if (status === 404) return false
      return failureCount < 3
    },
    select: (data) => Object.freeze({ ...data }),
  })
}
