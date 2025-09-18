<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const seed = ref('')

function genId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2, 10)
}

function startChat() {
  const text = seed.value.trim()
  if (!text) return
  const id = genId()

  router.push({ name: 'FlowPage', params: { id }, query: { q: text } })
}
</script>

<template>
  <section class="flex flex-col justify-center items-center w-full pb-20">
    <h1 class="text-3xl pb-9">Ready when you are.</h1>
    <Textarea class="!p-3 max-w-3xl w-full" rows="1" placeholder="Put your prompt..." auto-resize/>
  </section>
</template>

<style scoped></style>
