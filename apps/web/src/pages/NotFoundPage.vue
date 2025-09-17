<!-- src/pages/NotFoundPage.vue -->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import Button from 'primevue/button'

const router = useRouter()

function goHome() {
  router.push({ name: 'HomePage' })
}
</script>

<template>
  <section class="min-h-[70vh] flex items-center justify-center px-6">
    <div
      class="w-full max-w-xl rounded-2xl border
             border-gray-200/80 bg-white/80 shadow-lg backdrop-blur
             dark:border-gray-700/60 dark:bg-gray-900/70"
    >
      <div class="p-8">
        <h1
          class="text-6xl font-extrabold tracking-tight text-gray-900
                 dark:text-gray-100"
        >
          404
        </h1>
        <p
          class="mt-3 text-lg text-gray-600
                 dark:text-gray-400"
        >
          The page you’re looking for doesn’t exist or was moved.
        </p>

        <div class="mt-8">
          <Button
            label="Go home"
            icon="pi pi-home"
            class="px-5 py-2"
            @click="goHome"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped></style>
