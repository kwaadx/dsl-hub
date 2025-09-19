import {HttpMethod, RequestOptions} from './types';

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

export class HttpError extends Error {
  status: number;
  payload: any;
  url: string;
  method: HttpMethod;
  code?: string | number;

  constructor(params: {
    message: string;
    status: number;
    payload: any;
    url: string;
    method: HttpMethod;
    code?: string | number;
  }) {
    super(params.message);
    this.name = 'HttpError';
    this.status = params.status;
    this.payload = params.payload;
    this.url = params.url;
    this.method = params.method;
    this.code = params.code;
  }
}

export function isHttpError(e: unknown): e is HttpError {
  return e instanceof Error && (e as any).name === 'HttpError';
}

export async function http<TResp = unknown, TBody = unknown>(
  opts: RequestOptions<TBody>
): Promise<TResp> {
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
  try {
    if (ct.includes('application/json')) {
      data = await res.json();
    } else {
      const txt = await res.text();
      data = txt || null;
    }
  } catch {
    data = null;
  }

  if (!res.ok) {
    const message =
      (data && (data.message || data.error || data.detail)) ||
      `HTTP ${res.status} ${res.statusText}`;
    const code = data?.code ?? data?.errorCode;

    throw new HttpError({
      message,
      status: res.status,
      payload: data,
      url,
      method,
      code,
    });
  }

  return data as TResp;
}
