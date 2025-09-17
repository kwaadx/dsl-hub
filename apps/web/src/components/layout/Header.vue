<script setup lang="ts">
import {useThemeStore} from "@/store/theme";
import {useLayoutStore} from "@/store/layout";

const themeStore = useThemeStore();
const layoutStore = useLayoutStore();
</script>

<template>
  <header class="flex justify-between items-center p-3 bg-white/10 dark:bg-neutral-800/70">
    <Select
      optionLabel="name"
      placeholder="Select a City"
      :class="[
        layoutStore.sidebarVisible ? 'md:ml-0' : '',
        '!transition-all z-10 ml-10'
      ]"
    />
    <Button
      class="h-8"
      size="small"
      :icon="themeStore.isDark ? 'pi pi-sun' : 'pi pi-moon'"
      :severity="themeStore.isDark ? 'contrast' : 'secondary'"
      @click="themeStore.toggleDark()"
    ></Button>
  </header>
</template>

<style scoped>

</style>
