/**
 * Config store module
 *
 * This module handles application configuration.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ScreenDefaults {
  width: number;
  height: number;
  [key: string]: any;
}

interface Config {
  screen?: {
    defaults?: ScreenDefaults;
  };
  [key: string]: any;
}

export const useConfigStore = defineStore('config', () => {
  // State
  const config = ref<Config>({
    screen: {
      defaults: {
        width: 1920,
        height: 1080
      }
    }
  })
  const isLoading = ref(false)

  // Getters
  const screenDefaults = computed(() => config.value.screen?.defaults)

  // Actions
  async function fetchConfig() {
    isLoading.value = true
    try {
      // This would typically be an API call
      // For now, we'll use the default config
      return config.value
    } catch (error) {
      console.error('Failed to fetch config:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function showToast(toast: { severity: string; summary: string; detail?: string; life?: number }) {
    // This would typically trigger a toast notification
    // For now, we'll just log it
    console.log('Toast:', toast)
  }

  function setCommonError(error: any) {
    console.error('Common error:', error)
    showToast({
      severity: 'error',
      summary: 'Error',
      detail: error?.message || 'An unknown error occurred'
    })
  }

  return {
    // State
    config,
    isLoading,

    // Getters
    screenDefaults,

    // Actions
    fetchConfig,
    showToast,
    setCommonError
  }
})
