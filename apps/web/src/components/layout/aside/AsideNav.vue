<script lang="ts" setup>
import {computed, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useFlows} from '@/composables/data/flows/useFlows'
import {useDeleteFlow} from '@/composables/data/flows/useDeleteFlow'
import {useUpdateFlow} from '@/composables/data/flows/useUpdateFlow'
import AsideCreate from "@/components/layout/aside/AsideCreate.vue";
import {useQueryClient} from '@tanstack/vue-query'
import {qk} from '@/composables/data/queryKeys'

const route = useRoute()
const router = useRouter()
const props = defineProps<{ search?: string }>()

const {data, isLoading, isError, error} = useFlows()
const flows = computed(() => data?.value ?? [])

const {mutateAsync: deleteFlowAsync} = useDeleteFlow()
const {mutateAsync: updateFlowAsync} = useUpdateFlow()
const qc = useQueryClient()

async function onDelete(flow: { id: string; name: string; slug?: string }) {
  const ok = window.confirm(`Delete flow "${flow.name}"? This action cannot be undone.`)
  if (!ok) return
  const isCurrent = route.params.slug === flow.slug
  try {
    if (isCurrent) {
      // cancel any in-flight detail query to avoid 404 toast, then navigate home immediately
      await qc.cancelQueries({ queryKey: qk.flows.detail(flow.id) })
      await router.replace({ name: 'Home' })
    }
    await deleteFlowAsync({id: flow.id})
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

// Rename dialog state
const renameVisible = ref(false)
const current = ref<{ id: string; name: string; slug?: string } | null>(null)
const nameInput = ref('')
const slugInput = ref('')
const slugEdited = ref(false)
const isSubmitting = ref(false)
const errorMsg = ref('')

const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const slugValid = computed(() => !slugInput.value || slugPattern.test(slugInput.value))
const canSubmit = computed(() => {
  const trimmed = nameInput.value.trim()
  const changedName = current.value && trimmed && trimmed !== current.value.name
  const changedSlug = current.value && slugInput.value && slugInput.value !== (current.value.slug || '') && slugValid.value
  return !!(changedName || changedSlug) && !isSubmitting.value
})

function slugify(input: string) {
  return input
    .toLowerCase()
    .trim()
    .replace(/['"]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

watch(nameInput, (v) => {
  if (!slugEdited.value) slugInput.value = slugify(v || '')
})

function openRename(flow: { id: string; name: string; slug?: string }) {
  current.value = { ...flow }
  nameInput.value = flow.name
  slugInput.value = flow.slug || ''
  // if there is an existing slug, do not auto-overwrite when name changes
  slugEdited.value = !!flow.slug
  errorMsg.value = ''
  isSubmitting.value = false
  renameVisible.value = true
}

async function onRenameSave() {
  if (!current.value) return
  const id = current.value.id
  const oldSlug = current.value.slug || ''
  const patch: any = {}
  const trimmedName = nameInput.value.trim()
  if (trimmedName && trimmedName !== current.value.name) patch.name = trimmedName
  if (slugInput.value && slugInput.value !== (current.value.slug || '')) patch.slug = slugify(slugInput.value)
  if (!patch.name && !patch.slug) {
    // nothing to update
    renameVisible.value = false
    return
  }
  if (patch.slug && !slugPattern.test(patch.slug)) {
    errorMsg.value = 'Slug is invalid. Use lowercase letters, numbers and dashes.'
    return
  }
  isSubmitting.value = true
  errorMsg.value = ''
  try {
    const updated = await updateFlowAsync({ id, patch })
    // If the flow is currently open and slug changed, update URL to the new slug
    if (updated?.slug && updated.slug !== oldSlug && route.params.slug === oldSlug) {
      const name = (route.name as string) || 'Flow'
      await router.replace({ name, params: { ...route.params, slug: updated.slug } })
    }
    renameVisible.value = false
  } catch (e: any) {
    const msg = e?.message || 'Failed to update flow'
    errorMsg.value = /409|exists/i.test(String(msg)) ? 'Slug already exists. Try another.' : msg
  } finally {
    isSubmitting.value = false
  }
}

function onSlugInput() { slugEdited.value = true }

function menuItems(flow: { id: string; name: string; slug?: string }) {
  return [
    {
      label: 'Rename', icon: 'pi pi-pencil',
      command: () => openRename(flow)
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
    <div class="w-full px-3 flex justify-between items-center ">
      <div class="text-xl">Flows</div>
      <AsideCreate/>
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
          'bg-black/5 dark:bg-white/10 font-medium': route.params.slug === flow.slug,
          'bg-black/5 dark:bg-white/10': menuOpenStates[flow.id]
        }"
        class="h-12 group flex items-center rounded-md hover:bg-black/5 dark:hover:bg-white/10 select-none"
      >
        <RouterLink
          :to="{ name: 'FlowRoot', params: { slug: flow.slug } }"
          class="block w-full text-left px-3 py-2 truncate"
        >
          <span v-html="highlight(flow.name, props.search)"></span>
        </RouterLink>
        <Button
          :class="{
            '!hidden': !menuOpenStates[flow.id] && route.params.slug !== flow.slug
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
  <Dialog
    v-model:visible="renameVisible"
    modal
    header="Rename Flow"
    :style="{ width: '28rem' }"
  >
    <form class="space-y-4" @submit.prevent="onRenameSave">
      <div class="flex items-center gap-4">
        <label for="rename-name" class="font-semibold w-24">Name</label>
        <InputText
          id="rename-name"
          v-model="nameInput"
          class="flex-auto"
          autocomplete="off"
          placeholder="Flow name"
          :disabled="isSubmitting"
          autofocus
        />
      </div>

      <div class="flex items-start gap-4">
        <label for="rename-slug" class="font-semibold w-24">Slug</label>
        <div class="flex-1">
          <InputText
            id="rename-slug"
            v-model="slugInput"
            @input="onSlugInput"
            class="w-full"
            autocomplete="off"
            placeholder="(leave empty to keep)"
            :invalid="!!slugInput && !slugValid"
            :disabled="isSubmitting"
          />
          <p class="text-xs mt-1 text-surface-500 dark:text-surface-400">
            Leave empty to keep current. Allowed: <code>a-z</code>, <code>0-9</code>, dashes. Auto-updates from name
            until you start editing.
          </p>
        </div>
      </div>

      <div v-if="errorMsg" class="p-2 rounded bg-red-500/10 text-red-600 dark:text-red-400">
        {{ errorMsg }}
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <Button type="button" label="Cancel" severity="secondary" :disabled="isSubmitting" @click="renameVisible = false" />
        <Button type="submit" label="Save" :loading="isSubmitting" :disabled="!canSubmit" />
      </div>
    </form>
  </Dialog>
</template>
