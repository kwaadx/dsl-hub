/**
 * Auth store module
 *
 * This module handles authentication state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const isAuthenticating = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value)

  // Actions
  async function login(credentials: { username: string; password: string }) {
    isAuthenticating.value = true
    try {
      const response = await authService.login(credentials)
      token.value = response.token
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      isAuthenticating.value = false
    }
  }

  function logout() {
    token.value = null
  }

  async function refreshToken() {
    try {
      const response = await authService.refreshToken()
      token.value = response.token
      return response
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      throw error
    }
  }

  return {
    // State
    token,
    isAuthenticating,

    // Getters
    isAuthenticated,

    // Actions
    login,
    logout,
    refreshToken
  }
}, {
  persist: {
    key: 'auth-store',
    storage: localStorage,
    paths: ['token']
  }
})
