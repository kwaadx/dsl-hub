<script lang="ts" setup>
import Card from 'primevue/card'
import Tag from 'primevue/tag'

const props = defineProps<{
  card: {
    title: string
    description?: string
    image?: string
    url?: string
    meta?: Array<{ label: string; value: string }>
  }
}>()

const emit = defineEmits<{
  (e: 'open', url?: string): void
}>()
</script>

<template>
  <Card class="overflow-hidden">
    <template #header>
      <img v-if="card.image" :src="card.image" alt="preview" class="h-40 w-full object-cover"/>
    </template>
    <template #title>
      <div class="text-base font-semibold">{{ card.title }}</div>
    </template>
    <template #content>
      <p v-if="card.description" class="text-sm opacity-80">{{ card.description }}</p>
      <div v-if="card.meta?.length" class="mt-2 flex flex-wrap gap-2">
        <Tag v-for="m in card.meta" :key="m.label" :value="`${m.label}: ${m.value}`"/>
      </div>
    </template>
    <template #footer>
      <button
        v-if="card.url"
        class="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white"
        @click="$emit('open', card.url)"
      >
        Open
      </button>
    </template>
  </Card>
</template>
