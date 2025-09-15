/**
 * Widget store module
 *
 * This module handles widget state and operations.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Widget {
  id: string;
  type: string;
  title?: string;
  config?: any;
  [key: string]: any;
}

export const useWidgetStore = defineStore('widget', () => {
  // State
  const widgets = ref<Widget[]>([])
  const active = ref<Widget | null>(null)
  const current = ref<Widget | null>(null)

  // Actions
  function resetActive() {
    active.value = null
  }

  function resetCurrent() {
    current.value = null
  }

  function resetWidgets() {
    widgets.value = []
  }

  return {
    // State
    widgets,
    active,
    current,

    // Actions
    resetActive,
    resetCurrent,
    resetWidgets
  }
})
