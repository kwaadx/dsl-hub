/**
 * User store module
 *
 * This module handles user state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'

interface User {
  id: string;
  username: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  roles?: string[];
  [key: string]: any;
}

export const useUserStore = defineStore('user', () => {
  // State
  const current = ref<User | null>(null)
  const isLoading = ref(false)

  // Getters
  const currentId = computed(() => current.value?.id || null)
  const hasRole = computed(() => (role: string) =>
    current.value?.roles?.includes(role) || false
  )

  // Actions
  async function fetchCurrent() {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) {
      return null
    }

    isLoading.value = true
    try {
      // This would typically be an API call
      // For now, we'll simulate a successful response
      const mockUser: User = {
        id: '1',
        username: 'user',
        email: 'user@example.com',
        firstName: 'Test',
        lastName: 'User',
        roles: ['user']
      }

      current.value = mockUser
      return mockUser
    } catch (error) {
      console.error('Failed to fetch user:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function resetCurrent() {
    current.value = null
  }

  return {
    // State
    current,
    isLoading,

    // Getters
    currentId,
    hasRole,

    // Actions
    fetchCurrent,
    resetCurrent
  }
})
