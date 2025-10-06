<script lang="ts" setup>
import {ref, computed, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useUpdateFlow} from '@/composables/data/flows/useUpdateFlow'

const route = useRoute()
const router = useRouter()
const {mutateAsync: updateFlowAsync} = useUpdateFlow()

const visible = ref(false)
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

function open(flow: { id: string; name: string; slug?: string }) {
  current.value = {...flow}
  nameInput.value = flow.name
  slugInput.value = flow.slug || ''
  slugEdited.value = !!flow.slug
  errorMsg.value = ''
  isSubmitting.value = false
  visible.value = true
}

async function onSave() {
  if (!current.value) return
  const id = current.value.id
  const oldSlug = current.value.slug || ''
  const patch: any = {}
  const trimmedName = nameInput.value.trim()
  if (trimmedName && trimmedName !== current.value.name) patch.name = trimmedName
  if (slugInput.value && slugInput.value !== (current.value.slug || '')) patch.slug = slugify(slugInput.value)
  if (!patch.name && !patch.slug) {
    visible.value = false
    return
  }
  if (patch.slug && !slugPattern.test(patch.slug)) {
    errorMsg.value = 'Slug is invalid. Use lowercase letters, numbers and dashes.'
    return
  }
  isSubmitting.value = true
  errorMsg.value = ''
  try {
    const updated = await updateFlowAsync({id, patch})
    if (updated?.slug && updated.slug !== oldSlug && route.params.slug === oldSlug) {
      const name = (route.name as string) || 'Flow'
      await router.replace({name, params: {...route.params, slug: updated.slug}})
    }
    visible.value = false
  } catch (e: any) {
    const msg = e?.message || 'Failed to update flow'
    errorMsg.value = /409|exists/i.test(String(msg)) ? 'Slug already exists. Try another.' : msg
  } finally {
    isSubmitting.value = false
  }
}

function onSlugInput() {
  slugEdited.value = true
}

defineExpose({open})
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Rename Flow"
    :style="{ width: '28rem' }"
  >
    <form class="space-y-4" @submit.prevent="onSave">
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
            Leave empty to keep current. Allowed: <code>a-z</code>, <code>0-9</code>, dashes.
            Auto-updates from name
            until you start editing.
          </p>
        </div>
      </div>

      <div v-if="errorMsg" class="p-2 rounded bg-red-500/10 text-red-600 dark:text-red-400">
        {{ errorMsg }}
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <Button type="button" label="Cancel" severity="secondary" :disabled="isSubmitting"
                @click="visible = false"/>
        <Button type="submit" label="Save" :loading="isSubmitting" :disabled="!canSubmit"/>
      </div>
    </form>
  </Dialog>
</template>
