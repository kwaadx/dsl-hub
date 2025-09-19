<script setup lang="ts">
import Button from 'primevue/button'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
</script>

<template>
  <Button
    class="h-8"
    size="small"
    :icon="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"
    :severity="themeStore.isDark ? 'contrast' : 'secondary'"
    @click="themeStore.toggleDark()"
    aria-label="Toggle dark mode"
  />
</template>
