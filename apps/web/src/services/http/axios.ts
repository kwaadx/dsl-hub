import axios from 'axios'

const baseURL = (import.meta as any).env?.VITE_API_BASE_URL || (typeof window !== 'undefined' ? '' : '')

export const api = axios.create({
  baseURL,
  headers: {
    Accept: 'application/json',
  },
  withCredentials: false,
});

function getAuthTokenSafely(): string | null {
  try {
    // const { useAuthStore } = require('@/stores/auth')
    // return useAuthStore()?.token ?? null;
    return null
  } catch {
    return null
  }
}

function genIdempotencyKey(): string {
  // Prefer crypto.randomUUID when available
  try {
    const g = (globalThis as any);
    if (g?.crypto?.randomUUID) return g.crypto.randomUUID();
  } catch {}
  // Fallback RFC4122-ish v4
  const rnd = (n: number) => Math.floor(Math.random() * n);
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = rnd(16);
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

api.interceptors.request.use((config) => {
  const token = getAuthTokenSafely();
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as any)["Authorization"] = `Bearer ${token}`;
  }

  // Attach Content-Type for bodies
  if (config.data != null) {
    config.headers = config.headers ?? {}
    if (!(config.headers as any)["Content-Type"]) {
      (config.headers as any)["Content-Type"] = 'application/json';
    }
  }

  // Idempotency-Key for mutating requests, unless explicitly provided
  const method = (config.method || 'get').toLowerCase();
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    config.headers = config.headers ?? {};
    const hasKey = !!(config.headers as any)["Idempotency-Key"];
    if (!hasKey) {
      (config.headers as any)["Idempotency-Key"] = genIdempotencyKey();
    }
  }

  return config;
});

export default api
