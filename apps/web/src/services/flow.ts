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

export async function updateFlowApi(_id: string, _patch: Partial<Flow>, _signal?: AbortSignal): Promise<Flow> {
  const err = new Error('Updating flows is not supported by the backend yet');
  (err as any).code = 'NOT_IMPLEMENTED';
  (err as any).status = 501;
  throw err;
}

export async function deleteFlowApi(id: string, signal?: AbortSignal): Promise<void> {
  await http<void>({ method: 'DELETE', path: `/api/flows/${id}`, signal });
}

export async function fetchFlowsPagedApi(
  params: { page: number; pageSize?: number; q?: string },
  signal?: AbortSignal
): Promise<Paged<Flow>> {
  const { page, pageSize = 5, q = '' } = params;
  const all = await http<Flow[]>({ method: 'GET', path: '/api/flows', signal });
  const needle = q.trim().toLowerCase();
  const filtered = needle ? all.filter((f) => f.name.toLowerCase().includes(needle)) : all;
  const start = Math.max(0, (page - 1) * pageSize);
  const items = filtered.slice(start, start + pageSize);
  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  return { items, page, pageSize, totalItems, totalPages };
}
