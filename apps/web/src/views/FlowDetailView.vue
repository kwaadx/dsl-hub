<script setup lang="ts">
import { computed } from 'vue'
import { useFlowById } from '@/composables/data/flows/useFlowById'

const props = defineProps<{ id: string }>()
const id = computed(() => String(props.id ?? ''))

const { data: flow, isLoading, isError, error, refetch } = useFlowById(id)
</script>

<template>
  <section class="p-4 space-y-4">
    <div v-if="isLoading" class="animate-pulse space-y-2">
      <div class="h-6 w-48 bg-black/10 dark:bg-white/10 rounded"></div>
      <div class="h-4 w-80 bg-black/10 dark:bg-white/10 rounded"></div>
    </div>

    <div v-else-if="isError" class="p-3 rounded bg-red-500/10 text-red-600 dark:text-red-400">
      {{ (error as Error).message || 'Failed to load flow' }}
    </div>

    <div v-else class="space-y-3">
      <header class="flex items-center justify-between gap-2">
        <h1 class="text-xl font-semibold truncate">
          {{ flow?.name }}
        </h1>
        <div class="flex items-center gap-2">
          <RouterLink
            :to="{ name: 'Home' }"
            class="px-2 py-1 rounded bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20"
          >
            Back
          </RouterLink>
          <button
            class="px-2 py-1 rounded bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20"
            @click="refetch"
          >
            Refresh
          </button>
        </div>
      </header>

      <dl class="grid grid-cols-[auto,1fr] gap-x-4 gap-y-2">
        <dt class="text-gray-500">ID</dt>
        <dd class="font-mono text-sm break-all">{{ flow?.id }}</dd>

        <dt class="text-gray-500">Name</dt>
        <dd>{{ flow?.name }}</dd>
      </dl>
    </div>
  </section>
</template>
