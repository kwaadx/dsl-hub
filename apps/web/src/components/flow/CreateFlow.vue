<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCreateFlow } from '@/composables/data/flows/useCreateFlow'

const visible = ref(false)
const name = ref('')
const slug = ref('')
const isSubmitting = ref(false)
const errorMsg = ref('')

const canSubmit = computed(() => !!name.value && !isSubmitting.value)

const router = useRouter()
const create = useCreateFlow()

function resetForm() {
  name.value = ''
  slug.value = ''
  errorMsg.value = ''
}

async function onOpen() {
  resetForm()
}

async function onSave() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  errorMsg.value = ''
  try {
    const flow = await create.mutateAsync({ name: name.value, slug: slug.value || undefined })
    visible.value = false
    // Navigate to the flow root (will redirect to default mode)
    await router.push({ name: 'FlowRoot', params: { id: flow.id } })
  } catch (e: any) {
    errorMsg.value = e?.message || 'Failed to create flow'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Button icon="pi pi-plus" class="min-w-auto" @click="visible = true" />
  <Dialog v-model:visible="visible" modal header="Create Flow" :style="{ width: '25rem' }" @show="onOpen">
    <div class="flex items-center gap-4 mb-4">
      <label for="name" class="font-semibold w-24">name</label>
      <InputText id="name" v-model="name" class="flex-auto" autocomplete="off" placeholder="My new flow" />
    </div>
    <div class="flex items-center gap-4 mb-2">
      <label for="slug" class="font-semibold w-24">slug</label>
      <InputText id="slug" v-model="slug" class="flex-auto" autocomplete="off" placeholder="(optional)" />
    </div>
    <p class="text-xs text-surface-500 dark:text-surface-400 mb-6">Leave slug empty to auto-generate.</p>

    <div v-if="errorMsg" class="p-2 rounded bg-red-500/10 text-red-600 dark:text-red-400 mb-3">
      {{ errorMsg }}
    </div>

    <div class="flex justify-end gap-2">
      <Button type="button" label="Cancel" severity="secondary" :disabled="isSubmitting" @click="visible = false"></Button>
      <Button type="button" label="Save" :loading="isSubmitting" :disabled="!canSubmit" @click="onSave"></Button>
    </div>
  </Dialog>
</template>

<style scoped>

</style>
