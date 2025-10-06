<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCreateFlow } from '@/composables/data/flows/useCreateFlow'

const visible = ref(false)
const name = ref('')
const slug = ref('')
const isSubmitting = ref(false)
const errorMsg = ref('')
const slugEdited = ref(false)

const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/ // kebab-case
const slugValid = computed(() => !slug.value || slugPattern.test(slug.value))
const canSubmit = computed(() => !!name.value.trim() && !isSubmitting.value && slugValid.value)

const router = useRouter()
const create = useCreateFlow()

function resetForm() {
  name.value = ''
  slug.value = ''
  errorMsg.value = ''
  slugEdited.value = false
}

function onOpen() {
  resetForm()
}

function onHide() {
  resetForm()
}

function slugify(input: string) {
  return input
    .toLowerCase()
    .trim()
    .replace(/['"]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

watch(name, (v) => {
  if (!slugEdited.value) slug.value = slugify(v || '')
})

function onSlugInput() {
  slugEdited.value = true
}

async function onSave() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  errorMsg.value = ''
  try {
    const trimmedName = name.value.trim()
    const finalSlug = slug.value ? slugify(slug.value) : undefined
    const flow = await create.mutateAsync({ name: trimmedName, slug: finalSlug })
    visible.value = false
    await router.push({ name: 'FlowRoot', params: { slug: flow.slug } })
  } catch (e: any) {
    // опціонально: красивіше повідомлення для 409/validation
    const msg = e?.message || 'Failed to create flow'
    errorMsg.value = /409|exists/i.test(String(msg)) ? 'Slug already exists. Try another.' : msg
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Button icon="pi pi-plus" class="" @click="visible = true" link/>
  <Dialog
    v-model:visible="visible"
    modal
    header="Create Flow"
    :style="{ width: '25rem' }"
    @show="onOpen"
    @hide="onHide"
  >
    <form class="space-y-4" @submit.prevent="onSave">
      <div class="flex items-center gap-4">
        <label for="name" class="font-semibold w-24">Name</label>
        <InputText
          id="name"
          v-model="name"
          class="flex-auto"
          autocomplete="off"
          placeholder="My new flow"
          :disabled="isSubmitting"
          autofocus
        />
      </div>

      <div class="flex items-start gap-4">
        <label for="slug" class="font-semibold w-24">Slug</label>
        <div class="flex-1">
          <InputText
            id="slug"
            v-model="slug"
            @input="onSlugInput"
            class="w-full"
            autocomplete="off"
            placeholder="(optional)"
            :invalid="!!slug && !slugValid"
            :disabled="isSubmitting"
          />
          <p class="text-xs mt-1 text-surface-500 dark:text-surface-400">
            Leave empty to auto-generate. Allowed: <code>a-z</code>, <code>0-9</code>, dashes.
          </p>
        </div>
      </div>

      <div v-if="errorMsg" class="p-2 rounded bg-red-500/10 text-red-600 dark:text-red-400">
        {{ errorMsg }}
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <Button type="button" label="Cancel" severity="secondary" :disabled="isSubmitting" @click="visible = false" />
        <Button type="submit" label="Save" :loading="isSubmitting" :disabled="!canSubmit" />
      </div>
    </form>
  </Dialog>
</template>

<style scoped></style>
