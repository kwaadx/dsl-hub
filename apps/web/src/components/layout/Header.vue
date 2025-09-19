<script setup lang="ts">
import {ref} from 'vue';
import {useThemeStore} from "@/store/theme";
import {useLayoutStore} from "@/store/layout";

const themeStore = useThemeStore();
const layoutStore = useLayoutStore();

const cities = ref([
  {name: 'New York', code: 'NY'},
  {name: 'London', code: 'LDN'},
  {name: 'Paris', code: 'PRS'},
  {name: 'Tokyo', code: 'TKY'}
]);
const selectedCity = ref(null);
</script>

<template>
  <header class="flex justify-between items-center p-3 bg-white/10 dark:bg-neutral-800/70">
    <Select
      v-model="selectedCity"
      :options="cities"
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
      aria-label="Toggle dark mode"
    />
  </header>
</template>

