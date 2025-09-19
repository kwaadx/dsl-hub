<script lang="ts" setup>
import {computed, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useLayoutStore} from "@/store/layout";

type ModeKey = 'agent' | 'visual' | 'logs' | 'settings'
const ALLOWED: ModeKey[] = ['agent', 'visual', 'logs', 'settings']

const modes = [
  {name: 'Agent', code: 'agent' as ModeKey},
  {name: 'Visual', code: 'visual' as ModeKey},
  {name: 'Logs', code: 'logs' as ModeKey},
  {name: 'Settings', code: 'settings' as ModeKey},
]

const props = withDefaults(defineProps<{
  placeholder?: string
  items?: Array<{ name: string; code: ModeKey }>
}>(), {
  placeholder: 'Mode',
  items: undefined,
})

const route = useRoute()
const router = useRouter()
const layoutStore = useLayoutStore();

const model = ref<ModeKey | null>(null)

const hasValidContext = computed(() => {
  const id = route.params.id as string | undefined
  const m = route.params.mode as string | undefined
  return !!id && !!m && ALLOWED.includes(m as ModeKey)
})

function syncFromRoute() {
  if (!hasValidContext.value) {
    model.value = null
    return
  }
  const m = route.params.mode as ModeKey
  if (model.value !== m) model.value = m
}

syncFromRoute()
watch(() => route.params.mode, syncFromRoute)

watch(model, (val) => {
  if (!val || !hasValidContext.value) return
  const id = route.params.id as string
  if (route.params.mode === val) return
  const name = (route.name as string) || 'Flow'
  router.replace({name, params: {...route.params, id, mode: val}})
})

const options = computed(() => props.items ?? modes)

const selectPt = {
  label: {class: 'font-bold !text-md tracking-widest uppercase !text-neutral-400 !dark:text-neutral-400'},
}
</script>

<template>
  <Select
    v-if="hasValidContext"
    v-model="model"
    :class="[
      layoutStore.sidebarVisible ? 'md:ml-0' : '',
      '!transition-all z-10 ml-10 h-10'
    ]"
    :options="options"
    :placeholder="placeholder"
    :pt="selectPt"
    optionLabel="name"
    optionValue="code"
  />
</template>
