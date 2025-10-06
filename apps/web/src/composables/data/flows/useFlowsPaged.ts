import { computed, type MaybeRef, unref } from 'vue';
import { useQuery } from '@tanstack/vue-query';
import { fetchFlowsPagedApi, type Flow } from '@/services/flow';
import { qk } from '../queryKeys';

type PagedResult = { items: Flow[]; page: number; totalPages: number };
type Params = {
  page: MaybeRef<number>;
  pageSize?: MaybeRef<number | undefined>;
  q?: MaybeRef<string | undefined>;
};

export function useFlowsPaged(params: Params) {
  const page = computed(() => {
    const p = Number(unref(params.page));
    return Number.isFinite(p) && p > 0 ? p : 1;
  });

  const pageSize = computed(() => {
    const ps = unref(params.pageSize);
    return typeof ps === 'number' && ps > 0 ? ps : 20;
  });

  const q = computed(() => (unref(params.q) ?? '').trim());
  const enabled = computed(() => page.value > 0 && pageSize.value > 0);

  return useQuery<PagedResult>({
    queryKey: computed(() => qk.flows.paged(page.value, pageSize.value, { q: q.value })),
    queryFn: ({ signal }) => fetchFlowsPagedApi({ page: page.value, pageSize: pageSize.value, q: q.value }, signal),
    enabled,
    staleTime: 0,
    gcTime: 60_000,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  });
}
