import { http } from '@/core/http/http';

export interface Flow {
  id: string;
  name: string;
  slug?: string;
}

export interface Paged<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

function slugify(input: string): string {
  const s = input
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9\-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
  return s || `flow-${Math.random().toString(36).slice(2, 8)}`;
}

export async function fetchFlowsApi(signal?: AbortSignal): Promise<Flow[]> {
  return http<Flow[]>({ method: 'GET', path: '/api/flows', signal });
}

export async function fetchFlowByIdApi(id: string, signal?: AbortSignal): Promise<Flow> {
  return http<Flow>({ method: 'GET', path: `/api/flows/${id}`, signal });
}


export async function createFlowApi(
  payload: { name: string; slug?: string },
  signal?: AbortSignal
): Promise<Flow> {
  return http<Flow, { name: string; slug: string }>({
    method: 'POST',
    path: '/api/flows',
    body: { name: payload.name, slug: payload.slug ?? slugify(payload.name) },
    signal,
  });
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
    throw Object.assign(new Error('Nothing to update'), { status: 400, code: 'BAD_REQUEST' });
  }

  return http<Flow, { name?: string; slug?: string }>({
    method: 'PATCH',
    path: `/api/flows/${id}`,
    body,
    signal,
  });
}

export async function deleteFlowApi(id: string, signal?: AbortSignal): Promise<void> {
  await http<void>({ method: 'DELETE', path: `/api/flows/${id}`, signal });
}
