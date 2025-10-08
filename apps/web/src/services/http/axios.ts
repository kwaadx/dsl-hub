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

api.interceptors.request.use((config) => {
  const token = getAuthTokenSafely();
  if (token) {
    config.headers = config.headers ?? {}
    (config.headers as any)["Authorization"] = `Bearer ${token}`
  }

  if (config.data != null) {
    config.headers = config.headers ?? {}
    if (!(config.headers as any)["Content-Type"]) {
      (config.headers as any)["Content-Type"] = 'application/json'
    }
  }
  return config;
});

export default api
