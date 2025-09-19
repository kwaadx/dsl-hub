<script setup lang="ts">
import Button from 'primevue/button'
const props = defineProps<{ language?: string; code: string }>()

async function copy() {
  await navigator.clipboard.writeText(props.code)
}
</script>

<template>
  <div class="rounded-xl border border-neutral-200 bg-neutral-50 p-2 text-xs dark:border-neutral-700 dark:bg-neutral-900">
    <div class="mb-1 flex items-center justify-between">
      <div class="font-mono opacity-70">{{ language ?? 'text' }}</div>
      <Button size="small" icon="pi pi-copy" label="Copy" @click="copy" />
    </div>
    <pre class="overflow-auto rounded-md bg-black/80 p-3 text-[11px] leading-relaxed text-white"><code>{{ code }}</code></pre>
  </div>
</template>
