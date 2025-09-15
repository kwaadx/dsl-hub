/**
 * Workspace store module
 *
 * This module handles workspace state and operations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Workspace {
  id: string;
  title: string;
  screens?: string[];
  [key: string]: any;
}

export const useWorkspaceStore = defineStore('workspace', () => {
  // State
  const workspaces = ref<Workspace[]>([])
  const current = ref<Workspace | null>(null)

  // Getters
  const currentId = computed(() => current.value?.id || null)

  // Actions
  function resetCurrent() {
    current.value = null
  }

  function resetWorkspaces() {
    workspaces.value = []
  }

  return {
    // State
    workspaces,
    current,

    // Getters
    currentId,

    // Actions
    resetCurrent,
    resetWorkspaces
  }
})
