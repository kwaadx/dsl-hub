<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  error?: unknown
  fallback?: string
  size?: 'sm' | 'md'
  role?: string
}>(), {
  fallback: 'Something went wrong',
  size: 'md',
  role: 'alert',
})

const message = computed(() => {
  const e = props.error as any
  if (e == null || e === '') return props.fallback
  if (typeof e === 'string') return e
  if (e && typeof e.message === 'string') return e.message as string
  try {
    return JSON.stringify(e)
  } catch {
    return props.fallback
  }
})

const paddingClass = computed(() => (props.size === 'sm' ? 'p-2' : 'p-3'))
</script>

<template>
  <div :class="['rounded bg-red-500/10 text-red-600 dark:text-red-400', paddingClass]" :role="role">
    <slot>{{ message }}</slot>
  </div>
</template>
