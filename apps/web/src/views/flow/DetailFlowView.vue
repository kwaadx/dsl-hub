<script setup lang="ts">
import type { Flow } from '@/services/flow'

const props = defineProps<{ flow: Flow }>()
</script>

<template>
  <section class="w-full flex-1 min-h-0 flex flex-col">
    <div class="flex flex-1 min-h-0 flex-col gap-3 items-stretch" :key="`detail-flow-shell:${props.flow.id}`">
      <header class="shrink-0 flex items-center justify-between gap-2">
        <h1 class="text-xl font-semibold truncate">
          {{ props.flow.name }}
        </h1>
      </header>
      detail
    </div>
  </section>
</template>
