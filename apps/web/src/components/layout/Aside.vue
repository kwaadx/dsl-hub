<script lang="ts" setup>
import {ref} from 'vue'
import {useLayoutStore} from '@/store/layout';
import AsideHeader from "@/components/layout/aside/AsideHeader.vue";
import AsideSearch from "@/components/layout/aside/AsideSearch.vue";
import AsideNav from "@/components/layout/aside/AsideNav.vue";

const layoutStore = useLayoutStore();
const search = ref('')
</script>

<template>
  <aside
    :class="[
      'h-screen min-h-screen max-h-screen overflow-hidden flex flex-col backdrop-blur-sm bg-neutral-100 dark:bg-neutral-900 transition-all duration-300',
      { 'w-0 overflow-hidden': !layoutStore.sidebarVisible },
      'md:static md:flex fixed top-0 left-0 !z-50 md:z-auto',
      layoutStore.sidebarVisible ? 'w-[280px] shadow-lg md:shadow-none translate-x-0' : '-translate-x-full md:translate-x-0 md:w-0'
    ]"
    aria-label="Sidebar navigation"
  >
    <AsideHeader/>
    <AsideSearch v-model="search"/>
    <AsideNav :search="search"/>
  </aside>
</template>
