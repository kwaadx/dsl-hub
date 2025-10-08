<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type {Flow} from '@/services/flow'
import UiArrowBack from "@/components/UiArrowBack.vue";
import ThreadChat from '@/components/thread/chat/ThreadChat.vue'

const props = defineProps<{ flow: Flow }>()

const route = useRoute()
const threadId = computed(() => String(route.params.threadId ?? ''))

</script>

<template>
  <section class="w-full flex-1 min-h-0 flex flex-col">
    <div class="flex flex-1 min-h-0 flex-col gap-3 items-stretch"
         :key="`detail-flow-shell:${props.flow.id}`">
      <header class="shrink-0 flex flex-row items-center gap-2">
        <UiArrowBack/>
        <h1 class="text-xl font-semibold truncate">
          {{ props.flow.name }}
        </h1>
        <div class="ml-auto flex items-center gap-2">
          <span class="text-xs text-surface-500 dark:text-surface-400">Thread</span>
          <span class="font-mono text-xs px-2 py-0.5 rounded bg-surface-100 dark:bg-surface-800/60">
            {{ threadId }}
          </span>
        </div>
      </header>

      <ThreadChat :flow-id="props.flow.id" :thread-id="threadId" class="flex-1 min-h-0" />
    </div>
  </section>
</template>
