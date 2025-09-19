<script setup lang="ts">
import Button from 'primevue/button'

const props = defineProps<{
  actions: Array<{
    id: string
    label: string
    icon?: string
    kind?: 'primary' | 'secondary' | 'danger'
    payload?: Record<string, unknown>
    event?: string
  }>
}>()

const emit = defineEmits<{
  (e: 'act', ev: { kind: 'action.click'; actionId: string; payload?: unknown }): void
}>()

function styleOf(kind?: string) {
  switch (kind) {
    case 'danger':
      return {severity: 'danger' as const}
    case 'secondary':
      return {severity: 'secondary' as const, outlined: true}
    default:
      return {severity: 'primary' as const}
  }
}
</script>

<template>
  <div class="flex flex-wrap gap-2 rounded-2xl bg-neutral-100 p-2 dark:bg-neutral-800">
    <Button
      v-for="a in props.actions"
      :key="a.id"
      :icon="a.icon"
      :label="a.label"
      size="small"
      v-bind="styleOf(a.kind)"
      @click="$emit('act', { kind: 'action.click', actionId: a.id, payload: a.payload })"
    />
  </div>
</template>
