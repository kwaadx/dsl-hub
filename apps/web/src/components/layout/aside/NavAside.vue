<script setup lang="ts">
import {computed} from 'vue'
import {useRoute} from 'vue-router'
import {useFlows} from '@/composables/data/flows/useFlows'

const route = useRoute()
const props = defineProps<{ search?: string }>()

const {data, isLoading, isError, error} = useFlows()
const flows = computed(() => data?.value ?? [])

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlight(text: string, query?: string) {
  const q = (query ?? '').trim()
  if (!q) return escapeHtml(text)

  const re = new RegExp(escapeRegExp(q), 'ig')
  let last = 0
  let out = ''
  let m: RegExpExecArray | null

  while ((m = re.exec(text)) !== null) {
    out += escapeHtml(text.slice(last, m.index))
    out += `<mark class="px-0.5 rounded bg-yellow-200/70 dark:bg-yellow-500/40">${escapeHtml(m[0])}</mark>`
    last = re.lastIndex
  }
  out += escapeHtml(text.slice(last))
  return out
}

const filtered = computed(() => {
  const q = (props.search ?? '').trim().toLowerCase()
  if (!q) return flows.value
  return flows.value.filter(f => f.name.toLowerCase().includes(q))
})
</script>

<template>
  <nav class="p-2 space-y-1">
    <div v-if="isLoading" class="flex items-center mt-5">
      <ProgressSpinner aria-label="Loading" class="!h-15 !w-15"/>
    </div>
    <div v-else-if="isError" class="p-3 text-center text-red-500">
      {{ (error as Error).message }}
    </div>
    <template v-else>
      <div v-if="!filtered.length" class="p-3 text-center text-gray-500">
        {{ props.search ? 'Nothing found' : 'No flows yet' }}
      </div>
      <IconField
        v-for="flow in filtered"
        :key="flow.id"
        class="group flex items-center rounded-md hover:bg-black/5 dark:hover:bg-white/10"
        :class="{
          'bg-black/5 dark:bg-white/10 font-medium': route.params.id === flow.id
        }"
      >
        <RouterLink
          :to="{ name: 'FlowDetail', params: { id: flow.id } }"
          class="block w-full text-left px-3 py-2 truncate"
        >
          <span v-html="highlight(flow.name, props.search)"></span>
        </RouterLink>
        <InputIcon
          class="pi pi-ellipsis-v ml-2 !hidden group-hover:!inline-flex cursor-pointer text-gray-500"
        />
      </IconField>
    </template>
  </nav>
</template>
