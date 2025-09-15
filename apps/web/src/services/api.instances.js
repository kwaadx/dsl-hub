import axios from 'axios'

import store from '@/store'

const baseApi = axios.create({
  baseURL: import.meta.env.VITE_API_PATH,
  withCredentials: true,
})

// Request interceptor
baseApi.interceptors.request.use(
  (config) => {
    const workspaceId = store.getters['workspace/currentId']

    if (workspaceId) {
      config.headers['X-Workspace-ID'] = workspaceId
    }

    return config
  },
  (error) => {
    console.error('[api] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
baseApi.interceptors.response.use(
  (response) => {
    // Handle successful responses with error details
    if (response.data?.detail) {
      store.commit('setCommonError', response)
    }

    return response
  },
  async (error) => {
    const { response, config } = error

    // Handle 401 unauthorized errors
    if (response?.status === 401 && !config?.url?.includes('auth/login')) {
      store.commit('auth/logout')
      try {
        // Try to refresh token
        // await store.dispatch('auth/refreshToken')
        // Retry the original request
        // return baseApi(config)
      } catch (refreshError) {
        // If refresh fails, logout user
        console.error('[api] Token refresh failed:', refreshError)
        store.commit('auth/logout')
      }
    }

    // Handle error responses with detail
    if (response?.data?.detail) {
      store.commit('setCommonError', response)
    }

    // Log error for debugging
    console.error('[api] Response error:', {
      status: response?.status,
      url: config?.url,
      method: config?.method,
      error: error.message,
    })

    return Promise.reject(error)
  }
)

export default baseApi
