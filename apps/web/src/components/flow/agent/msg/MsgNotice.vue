<script lang="ts" setup>
import Tag from 'primevue/tag'

const props = withDefaults(defineProps<{
  severity?: 'info' | 'warn' | 'success' | 'error';
  text: string
}>(), {
  severity: 'info'
})
const sevMap: Record<string, any> = {
  info: {severity: 'info'},
  warn: {severity: 'warning'},
  success: {severity: 'success'},
  error: {severity: 'danger'},
}
</script>

<template>
  <Tag :value="text" v-bind="sevMap[severity]"/>
</template>
