/**
 * Screen store module
 *
 * This module handles screen state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface ScreenDefaults {
  width: number;
  height: number;
  [key: string]: any;
}

interface Screen {
  id: string;
  title: string;
  pages?: string[];
  width?: number;
  height?: number;
  [key: string]: any;
}

export const useScreenStore = defineStore('screen', () => {
  // State
  const screens = ref<Screen[]>([])
  const current = ref<Screen | null>(null)
  const defaultSettings = ref<ScreenDefaults>({
    width: 1920,
    height: 1080
  })

  // Getters
  const currentId = computed(() => current.value?.id || null)

  // Actions
  function resetCurrent() {
    current.value = null
  }

  function resetScreens() {
    screens.value = []
  }

  function setDefault(defaults: ScreenDefaults) {
    defaultSettings.value = defaults
  }

  return {
    // State
    screens,
    current,
    defaultSettings,

    // Getters
    currentId,

    // Actions
    resetCurrent,
    resetScreens,
    setDefault
  }
})
