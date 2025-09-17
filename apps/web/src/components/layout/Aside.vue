<script setup lang="ts">
import { useLayoutStore } from '@/store/layout';
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
      'desktop-aside'
    ]"
    aria-label="Sidebar navigation"
  >
    <HeaderAside/>
    <SearchAside/>
    <NavAside/>
  </aside>
</template>

<style scoped>
@media (max-width: 768px) {
  .desktop-aside {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 50;
    width: 280px !important;
    transform: translateX(-100%);
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
  }

  .desktop-aside:not(.w-0) {
    transform: translateX(0);
  }
}
</style>
