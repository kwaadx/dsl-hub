<script setup lang="ts">
import { useLayoutStore } from '@/store/layout'

const layoutStore = useLayoutStore()
</script>

<template>
  <div class="p-3 flex justify-between items-center">
    <img class="h-10" src="@/assets/images/logo.png"  alt="Logo"/>
    <i class="!text-2xl cursor-pointer pi pi-bars" @click="layoutStore.toggleSidebar"/>
  </div>
</template>

<style scoped>

</style>
