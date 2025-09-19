<script lang="ts" setup>
import {useLayoutStore} from '@/store/layout'

const layoutStore = useLayoutStore()
</script>

<template>
  <div class="p-3 flex justify-between items-center">
    <RouterLink
      :to="{ name: 'Home' }"
      aria-label="Go to Home"
      class="inline-flex items-center cursor-pointer"
    >
      <img alt="Logo" class="h-10 select-none" src="@/assets/images/logo.png"/>
    </RouterLink>

    <i class="!text-2xl cursor-pointer pi pi-bars" @click="layoutStore.toggleSidebar"/>
  </div>
</template>
