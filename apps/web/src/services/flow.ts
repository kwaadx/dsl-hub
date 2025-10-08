import api from '@/services/http/axios';
import type {Flow} from '@/types/flow';
import {slugify} from '@/utils/slugify';

export type {Flow};

export async function fetchFlowsApi(signal?: AbortSignal): Promise<Flow[]> {
  const {data} = await api.get<Flow[]>('/api/flows', {signal});
  return data;
}

export async function fetchFlowByIdApi(id: string, signal?: AbortSignal): Promise<Flow> {
  const {data} = await api.get<Flow>(`/api/flows/${id}`, {signal});
  return data;
}

export async function createFlowApi(
  payload: { name: string; slug?: string },
  signal?: AbortSignal
): Promise<Flow> {
  const slug = (payload.slug ?? slugify(payload.name)) || `flow-${Math.random().toString(36).slice(2, 8)}`;
  const body = {name: payload.name, slug};
  const {data} = await api.post<Flow>('/api/flows', body, {signal});
  return data;
}

export async function updateFlowApi(
  id: string,
  patch: Partial<Flow>,
  signal?: AbortSignal
): Promise<Flow> {
  const body: Record<string, unknown> = {};
  if (typeof patch.name === 'string') body.name = patch.name;
  if (typeof patch.slug === 'string') body.slug = patch.slug;

  if (!('name' in body) && !('slug' in body)) {
    throw Object.assign(new Error('Nothing to update'), {status: 400, code: 'BAD_REQUEST'});
  }

  const {data} = await api.patch<Flow>(`/api/flows/${id}`, body, {signal});
  return data;
}

export async function deleteFlowApi(id: string, signal?: AbortSignal): Promise<void> {
  await api.delete(`/api/flows/${id}`, {signal});
}
