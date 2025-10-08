import {useMutation} from '@tanstack/vue-query';
import {createThreadForFlowApi, type Thread} from '@/services/thread';

export function useCreateThread() {
  return useMutation({
    mutationFn: ({ flowId, signal }: { flowId: string; signal?: AbortSignal }) =>
      createThreadForFlowApi(flowId, signal),
  });
}
