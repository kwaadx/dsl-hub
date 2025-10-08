import api from '@/services/http/axios';
import type {Thread} from '@/types/thread';

export type {Thread};

export async function createThreadForFlowApi(
  flowId: string,
  signal?: AbortSignal
): Promise<Thread> {
  const {data} = await api.post<Thread>(`/api/flows/${flowId}/threads`, undefined, {signal});
  return data;
}

export async function fetchThreadsForFlowApi(
  flowId: string,
  signal?: AbortSignal
): Promise<Thread[]> {
  const {data} = await api.get<Thread[]>(`/api/flows/${flowId}/threads`, {signal});
  return data;
}
