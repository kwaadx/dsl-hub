<template>
  <Toast/>
  <component :is="layout">
    <router-view/>
  </component>
</template>

<script setup lang="ts">
import {computed, type Component, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {useTheme} from '@primevue/themes'
import {AuraPreset} from '@/theme/aura'
import layoutDefault from '@/layouts/default.vue'

const route = useRoute()
const layout = computed<Component>(() => route.meta.layout ?? layoutDefault)

useTheme({
  preset: AuraPreset,
  options: {
    darkModeSelector: '.theme-dark',
  },
})

onMounted(() => {
  const saved = localStorage.getItem('theme:dark')
  const prefersDark =
    window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches

  const dark = saved !== null ? saved === '1' : prefersDark
  document.documentElement.classList.toggle('theme-dark', dark)
})
</script>

<style scoped></style>
