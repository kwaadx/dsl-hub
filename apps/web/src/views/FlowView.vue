<script setup lang="ts">
import { computed } from 'vue'
import { useFlowById } from '@/composables/data/flows/useFlowById'
import AgentFlow from '@/components/flow/AgentFlow.vue'

const props = defineProps<{ id: string; mode?: string }>()
const id = computed(() => String(props.id ?? ''))
const mode = computed(() => props.mode ?? 'agent')

const { data: flow, isLoading, isError, error } = useFlowById(id)
</script>

<template>
  <section class="w-full flex-1 min-h-0 flex flex-col">
    <div v-if="isLoading" class="animate-pulse space-y-2">
      <div class="h-6 w-48 bg-black/10 dark:bg-white/10 rounded"></div>
      <div class="h-4 w-80 bg-black/10 dark:bg-white/10 rounded"></div>
    </div>

    <div v-else-if="isError" class="p-3 rounded bg-red-500/10 text-red-600 dark:text-red-400">
      {{ (error as Error).message || 'Failed to load flow' }}
    </div>

    <div
      v-else
      class="flex flex-1 min-h-0 flex-col gap-3 items-stretch"
      :key="`flow-shell:${id}:${mode}`"
    >
      <header class="shrink-0 flex items-center justify-between gap-2">
        <h1 class="text-xl font-semibold truncate">
          {{ flow?.name }}
        </h1>
      </header>

      <div v-if="mode === 'agent'" class="flex-1 min-h-0 overflow-hidden">
        <AgentFlow :key="`agent:${id}`" :flowId="id" />
      </div>
    </div>
  </section>
</template>
