<script setup lang="ts">
import {useLayoutStore} from '@/store/layout';
import HeaderAside from "@/components/layout/aside/HeaderAside.vue";
import SearchAside from "@/components/layout/aside/SearchAside.vue";
import NavAside from "@/components/layout/aside/NavAside.vue";

const layoutStore = useLayoutStore();
</script>

<template>
  <aside
    :class="[
      'h-full backdrop-blur-sm overflow-y-auto bg-neutral-100 dark:bg-neutral-900 transition-all duration-300',
      { 'w-0 overflow-hidden': !layoutStore.sidebarVisible },
      'md:static md:block fixed top-0 left-0 !z-50 md:z-auto',
      layoutStore.sidebarVisible ? 'w-[280px] shadow-lg md:shadow-none translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0'
    ]"
    aria-label="Sidebar navigation"
  >
    <HeaderAside/>
    <SearchAside/>
    <NavAside/>
  </aside>
</template>
