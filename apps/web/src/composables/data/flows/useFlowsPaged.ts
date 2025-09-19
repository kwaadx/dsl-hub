import {computed, type MaybeRef, unref} from 'vue';
import {keepPreviousData, useQuery} from '@tanstack/vue-query';
import {fetchFlowsPagedApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';

type PagedResult = { items: Flow[]; page: number; totalPages: number };
type Params = {
  page: MaybeRef<number>;
  pageSize?: MaybeRef<number | undefined>;
  q?: MaybeRef<string | undefined>;
};

export function useFlowsPaged(params: Params) {
  const page = computed(() => Number(unref(params.page)));
  const pageSize = computed(() => unref(params.pageSize));
  const q = computed(() => unref(params.q) ?? '');

  return useQuery<PagedResult>({
    queryKey: computed(() => qk.flows.paged(page.value, pageSize.value, {q: q.value})),
    queryFn: () => fetchFlowsPagedApi({page: page.value, q: q.value}),
    placeholderData: keepPreviousData,
  });
}
