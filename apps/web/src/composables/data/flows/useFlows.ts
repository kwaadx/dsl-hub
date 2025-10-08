import {useQuery, keepPreviousData} from '@tanstack/vue-query';
import {fetchFlowsApi, type Flow} from '@/services/flow';
import {qk} from '../queryKeys';
import { retry404Safe } from '@/lib/retry';

export function useFlows() {
  return useQuery<Flow[]>({
    queryKey: qk.flows.list(),
    queryFn: ({signal}) => fetchFlowsApi(signal),
    staleTime: 0,
    gcTime: 60_000,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    placeholderData: keepPreviousData,
    retry: retry404Safe,
    select: (data) => Object.freeze([...(data ?? [])]) as unknown as Flow[],
  });
}
