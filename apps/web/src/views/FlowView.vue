<script setup lang="ts">
import {computed, watch} from 'vue'
import {useFlows} from '@/composables/data/flows/useFlows'
import {useFlowById} from '@/composables/data/flows/useFlowById'
import {useRouter} from 'vue-router'
import UiLoadingDots from '@/components/UiLoadingDots.vue'

const props = defineProps<{ slug: string }>()
const slug = computed(() => String(props.slug ?? ''))

const {data: flows, isLoading: flowsLoading} = useFlows()
const id = computed(() => {
  const list = flows?.value ?? []
  const found = list.find(f => f.slug === slug.value)
  return found?.id ?? ''
})

const {data: flow, isLoading: flowByIdLoading, isError, error} = useFlowById(id)
const router = useRouter()

watch([flows, flowsLoading, slug], ([flowsVal, loading, slugVal]) => {
  if (loading) return
  const list = flowsVal ?? []
  if (Array.isArray(list)) {
    const found = list.find(f => f.slug === slugVal)
    if (!found) {
      router.replace({name: 'NotFound'})
    }
  }
}, { immediate: true })
</script>

<template>
  <section class="w-full flex-1 min-h-0 flex flex-col">
    <div v-if="flowByIdLoading || flowsLoading || !flow" class="p-6 flex items-center justify-center">
      <UiLoadingDots />
    </div>

    <div v-else-if="isError" class="p-3 rounded bg-red-500/10 text-red-600 dark:text-red-400">
      {{ (error as Error).message || 'Failed to load flow' }}
    </div>

    <router-view v-else v-slot="{ Component }">
      <component v-if="Component" :is="Component" :flow="flow"/>
      <div v-else
        class="flex flex-1 min-h-0 flex-col gap-3 items-stretch"
        :key="`detail-flow-shell:${id}`"
      >
        <header class="shrink-0 flex items-center justify-between gap-2">
          <h1 class="text-xl font-semibold truncate">
            {{ flow?.name }}
          </h1>
        </header>

        <nav class="shrink-0 flex items-center gap-4">
          <Button @click="router.push({name: 'DetailFlow'})" class="text-primary-600 hover:underline">Details</Button>
          <Button @click="router.push({name: 'PipelineFlow'})" class="text-primary-600 hover:underline">Pipelines</Button>
          <Button @click="router.push({name: 'ThreadFlow'})" class="text-primary-600 hover:underline">Threads</Button>
        </nav>
      </div>
    </router-view>
  </section>
</template>
