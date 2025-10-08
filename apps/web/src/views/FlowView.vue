<script setup lang="ts">
import {computed, watch} from 'vue'
import {useFlows} from '@/composables/data/flows/useFlows'
import {useFlowById} from '@/composables/data/flows/useFlowById'
import {useRouter} from 'vue-router'
import UiLoadingDots from '@/components/UiLoadingDots.vue'
import UiErrorAlert from '@/components/UiErrorAlert.vue'
import CreateThreadButton from '@/components/thread/CreateThreadButton.vue'
import ThreadsList from '@/components/thread/ThreadsList.vue'

const props = defineProps<{ slug: string }>()
const slug = computed(() => String(props.slug ?? ''))

const {data: flows, isLoading: flowsLoading, isError: flowsError, error: flowsErr} = useFlows()

const foundFlow = computed(() => {
  const list = flows?.value ?? []
  return Array.isArray(list) ? list.find(f => f.slug === slug.value) : undefined
})

const id = computed(() => foundFlow.value?.id ?? '')

const {data: flow, isLoading: flowByIdLoading, isError, error} = useFlowById(id)

const router = useRouter()

watch([flows, flowsLoading, slug], ([flowsVal, loading]) => {
  if (loading) return
  const exists = (flowsVal ?? []).some((f: any) => f.slug === slug.value)
  if (!exists) router.replace({name: 'NotFound'})
}, {immediate: true})
</script>

<template>
  <section class="w-full flex-1 min-h-0 flex flex-col">
    <UiErrorAlert v-if="flowsError" :error="flowsErr" fallback="Failed to load flows"/>

    <div
      v-else-if="flowsLoading || flowByIdLoading || (!foundFlow && !flowsLoading)"
      class="p-6 flex items-center justify-center"
    >
      <UiLoadingDots/>
    </div>

    <UiErrorAlert v-else-if="isError" :error="error" fallback="Failed to load flow"/>

    <router-view v-else :key="id" v-slot="{ Component }">
      <component v-if="Component" :is="Component" :flow="flow"/>
      <div
        v-else
        :key="`detail-flow-shell:${id}`"
        class="flex flex-1 min-h-0 flex-col gap-3 items-stretch"
      >
        <h1 class="text-xl font-semibold truncate">
          {{ flow?.name }}
        </h1>
        <div class="relative">
          <ThreadsList :flow-id="flow!.id"/>
          <CreateThreadButton class="!absolute !-top-2 !right-0" :flow="flow!"/>
        </div>
      </div>
    </router-view>
  </section>
</template>
