<script setup lang="ts">
import {ref, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useCreateFlow} from '@/composables/data/flows/useCreateFlow'
import {useNameSlugSync} from '@/composables/forms/useNameSlugSync'
import UiErrorAlert from '@/components/UiErrorAlert.vue'

const visible = ref(false)
const name = ref('')
const {slug, slugEdited, slugValid, slugify, onSlugInput} = useNameSlugSync(name)
const isSubmitting = ref(false)
const errorMsg = ref('')

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

async function onSave() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  errorMsg.value = ''
  try {
    const trimmedName = name.value.trim()
    const finalSlug = slug.value ? slugify(slug.value) : undefined
    const flow = await create.mutateAsync({name: trimmedName, slug: finalSlug})
    visible.value = false
    await router.push({name: 'Flow', params: {slug: flow.slug}})
  } catch (e: any) {
    const msg = e?.message || 'Failed to create flow'
    errorMsg.value = /409|exists/i.test(String(msg)) ? 'Slug already exists. Try another.' : msg
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="p-3 flex justify-end items-center gap-3">
    <div class="text-gray-500">New Flow</div>
    <Button icon="pi pi-plus" @click="visible = true" rounded size="small"/>
  </div>

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

      <UiErrorAlert v-if="errorMsg" :error="errorMsg" size="sm" />

      <div class="flex justify-end gap-2 pt-2">
        <Button type="button" label="Cancel" severity="secondary" :disabled="isSubmitting"
                @click="visible = false"/>
        <Button type="submit" label="Save" :loading="isSubmitting" :disabled="!canSubmit"/>
      </div>
    </form>
  </Dialog>
</template>

<style scoped></style>
