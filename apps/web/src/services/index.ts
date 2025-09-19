export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestOptions<TBody = unknown> {
  method?: HttpMethod;
  path: string;
  body?: TBody;
  query?: Record<string, any>;
  headers?: Record<string, string>;
  signal?: AbortSignal | null;
  auth?: boolean;
}

const BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' ? '' : '');

function buildUrl(path: string, query?: Record<string, any>) {
  const url = new URL(path, BASE_URL || window.location.origin);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      url.searchParams.set(k, String(v));
    });
  }
  return url.toString();
}

function getAuthTokenSafely(): string | null {
  try {
    // const { useAuthStore } = require('@/stores/auth');
    // return useAuthStore()?.token ?? null;
    return null;
  } catch {
    return null;
  }
}

export async function http<TResp = unknown, TBody = unknown>(opts: RequestOptions<TBody>): Promise<TResp> {
  const {
    method = 'GET',
    path,
    body,
    query,
    headers = {},
    signal = null,
    auth = false,
  } = opts;

  const url = buildUrl(path, query);

  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...headers,
  };

  const hasBody = body !== undefined && body !== null && method !== 'GET';
  if (hasBody && !finalHeaders['Content-Type']) {
    finalHeaders['Content-Type'] = 'application/json';
  }

  if (auth) {
    const token = getAuthTokenSafely();
    if (token) finalHeaders['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method,
    headers: finalHeaders,
    body: hasBody ? JSON.stringify(body) : undefined,
    signal: signal ?? undefined,
  });

  if (res.status === 204) return undefined as unknown as TResp;

  let data: any = null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (!res.ok) {
    const message =
      (data && (data.message || data.error || data.detail)) ||
      `HTTP ${res.status} ${res.statusText}`;
    const err = new Error(message) as Error & { status?: number; payload?: any };
    err.status = res.status;
    err.payload = data;
    throw err;
  }

  return data as TResp;
}
