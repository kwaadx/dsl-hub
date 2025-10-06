<script lang="ts" setup>
import {computed, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useFlows} from '@/composables/data/flows/useFlows'
import {useDeleteFlow} from '@/composables/data/flows/useDeleteFlow'
import CreateFlow from "@/components/flow/CreateFlow.vue";

const route = useRoute()
const router = useRouter()
const props = defineProps<{ search?: string }>()

const {data, isLoading, isError, error} = useFlows()
const flows = computed(() => data?.value ?? [])

const { mutateAsync: deleteFlowAsync } = useDeleteFlow()

async function onDelete(flow: { id: string; name: string }) {
  const ok = window.confirm(`Delete flow "${flow.name}"? This action cannot be undone.`)
  if (!ok) return
  try {
    await deleteFlowAsync({ id: flow.id })
    if (route.params.id === flow.id) {
      await router.push({ name: 'Home' })
    }
  } catch (e: any) {
    const msg = e?.message || 'Failed to delete the flow'
    // Use a simple alert for minimal change; could be replaced with a Toast later
    window.alert(msg)
  }
}

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlight(text: string, query?: string) {
  const q = (query ?? '').trim();
  if (!q) return escapeHtml(text)
  const re = new RegExp(escapeRegExp(q), 'ig')
  let last = 0, out = '', m: RegExpExecArray | null
  while ((m = re.exec(text)) !== null) {
    out += escapeHtml(text.slice(last, m.index))
    out += `<mark class="px-0.5 rounded bg-yellow-200/70 dark:bg-yellow-500/40">${escapeHtml(m[0])}</mark>`
    last = re.lastIndex
  }
  out += escapeHtml(text.slice(last));
  return out
}

const filtered = computed(() => {
  const q = (props.search ?? '').trim().toLowerCase()
  if (!q) return flows.value
  return flows.value.filter(f => f.name.toLowerCase().includes(q))
})

function menuItems(flow: { id: string; name: string }) {
  return [
    {
      label: 'Open', icon: 'pi pi-external-link',
      command: () => router.push({name: 'FlowRoot', params: {id: flow.id}})
    },
    {separator: true},
    {
      label: 'Rename', icon: 'pi pi-pencil',
      command: () => console.log('Rename', flow)
    },
    {
      label: 'Delete', icon: 'pi pi-trash',
      command: () => onDelete(flow)
    },
  ]
}

type TieredMenuInst = ComponentPublicInstance & TieredMenuMethods

const menuRefs = ref<Record<string, TieredMenuInst | null>>({})

function setMenuRef(id: string, el: Element | ComponentPublicInstance | null) {
  const inst = el as unknown as TieredMenuInst | null
  if (inst) menuRefs.value[id] = inst
  else delete menuRefs.value[id]
}

function openMenu(evt: Event, flow: { id: string; name: string }) {
  const inst = menuRefs.value[flow.id]
  inst?.toggle(evt)
}

const menuOpenStates = ref<Record<string, boolean>>({})

function setOpen(flowId: string, value: boolean) {
  menuOpenStates.value[flowId] = value
}
</script>

<template>
  <nav class="p-3 space-y-1">
    <div>
      <CreateFlow/>
    </div>
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

      <div
        v-for="flow in filtered"
        :key="flow.id"
        :class="{
          'bg-black/5 dark:bg-white/10 font-medium': route.params.id === flow.id,
          'bg-black/5 dark:bg-white/10': menuOpenStates[flow.id]
        }"
        class="h-12 group flex items-center rounded-md hover:bg-black/5 dark:hover:bg-white/10 select-none"
      >
        <RouterLink
          :to="{ name: 'FlowRoot', params: { id: flow.id } }"
          class="block w-full text-left px-3 py-2 truncate"
        >
          <span v-html="highlight(flow.name, props.search)"></span>
        </RouterLink>
        <Button
          :class="{
            '!hidden': !menuOpenStates[flow.id] && route.params.id !== flow.id
          }"
          class="ml-2 p-1 rounded group-hover:!flex items-center justify-center cursor-pointer"
          icon="pi pi-ellipsis-v"
          link

          @click.stop="openMenu($event, flow)"
        ></Button>
        <TieredMenu
          :ref="(el) => setMenuRef(flow.id, el)"
          :model="menuItems(flow)"
          appendTo="self"
          popup
          @hide="setOpen(flow.id, false)"
          @show="setOpen(flow.id, true)"
        />
      </div>
    </template>
  </nav>
</template>
