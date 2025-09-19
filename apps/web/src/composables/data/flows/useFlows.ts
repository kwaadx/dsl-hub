import { useQuery } from '@tanstack/vue-query';
import { fetchFlowsApi, type Flow } from '@/services/flow';
import { qk } from '../queryKeys';

export function useFlows() {
  return useQuery<Flow[]>({
    queryKey: qk.flows.list(),
    queryFn: ({ signal }) => fetchFlowsApi(signal),
    staleTime: 60_000,
    refetchOnWindowFocus: true,
  });
}
