<script setup lang="ts">
import { useLayoutStore } from '@/store/layout'
const layoutStore = useLayoutStore()
</script>

<template>
  <div class="p-3 flex justify-between items-center">
    <RouterLink
      :to="{ name: 'Home' }"
      class="inline-flex items-center cursor-pointer"
      aria-label="Go to Home"
    >
      <img class="h-10 select-none" src="@/assets/images/logo.png" alt="Logo" />
    </RouterLink>

    <i class="!text-2xl cursor-pointer pi pi-bars" @click="layoutStore.toggleSidebar" />
  </div>
</template>
