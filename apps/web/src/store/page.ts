/**
 * Page store module
 *
 * This module handles page state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Page {
  id: string;
  title: string;
  widgets?: string[];
  [key: string]: any;
}

export const usePageStore = defineStore('page', () => {
  // State
  const pages = ref<Page[]>([])
  const current = ref<Page | null>(null)

  // Getters
  const currentId = computed(() => current.value?.id || null)

  // Actions
  function resetCurrent() {
    current.value = null
  }

  function resetPages() {
    pages.value = []
  }

  return {
    // State
    pages,
    current,

    // Getters
    currentId,

    // Actions
    resetCurrent,
    resetPages
  }
})
