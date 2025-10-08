import {useMutation, useQueryClient} from '@tanstack/vue-query';
import {createThreadForFlowApi, type Thread} from '@/services/thread';
import {qk} from '../queryKeys';
import { retry404Safe } from '@/lib/retry';

export function useCreateThread() {
  const queryClient = useQueryClient();
  return useMutation<Thread, Error, { flowId: string; signal?: AbortSignal }>({
    mutationFn: ({ flowId, signal }) => createThreadForFlowApi(flowId, signal),
    retry: retry404Safe,
    onSuccess: (created, variables) => {
      const flowId = variables.flowId;
      queryClient.setQueryData<Thread[]>(qk.threads.list(flowId), (old) => {
        const list = Array.isArray(old) ? old : [];
        const exists = list.some((t) => (t as any).id === created.id);
        return exists ? list : [created, ...list];
      });
      queryClient.invalidateQueries({ queryKey: qk.threads.list(flowId) });
    },
  });
}
