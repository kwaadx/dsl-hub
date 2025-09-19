<script lang="ts" setup>
import Button from 'primevue/button'
import {useThemeStore} from '@/store/theme'

const themeStore = useThemeStore()
</script>

<template>
  <Button
    :icon="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"
    :severity="themeStore.isDark ? 'contrast' : 'secondary'"
    aria-label="Toggle dark mode"
    class="h-8"
    size="small"
    @click="themeStore.toggleDark()"
  />
</template>
