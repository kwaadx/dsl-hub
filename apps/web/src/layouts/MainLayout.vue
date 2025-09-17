<script setup lang="ts">
import {useLayoutStore} from '@/store/layout';
import Aside from "@/components/layout/Aside.vue";
import Header from "@/components/layout/Header.vue";
import Main from "@/components/layout/Main.vue";
import Footer from "@/components/layout/Footer.vue";

const layoutStore = useLayoutStore();
</script>

<template>
  <div class="h-screen w-full bg-neutral-50 dark:bg-neutral-900">
    <div class="main-layout grid h-full transition-all duration-300"
         :class="layoutStore.sidebarVisible ? 'grid-cols-[280px_1fr]' : 'grid-cols-[0px_1fr]'">
      <Aside/>
      <div class="flex h-full flex-col">
        <Header/>
        <Main>
          <slot/>
        </Main>
        <Footer/>
      </div>
    </div>

    <div v-if="!layoutStore.sidebarVisible" class="fixed top-4 left-3 z-40">
      <i class="!text-2xl cursor-pointer pi pi-bars" @click="layoutStore.toggleSidebar"/>
    </div>

    <div
      v-if="layoutStore.sidebarVisible"
      class="fixed inset-0 bg-black/50 z-40 md:hidden"
      @click="layoutStore.toggleSidebar"
    ></div>
  </div>
</template>

<style scoped>
@media (max-width: 768px) {
  .main-layout {
    grid-template-columns: 1fr !important;
  }
}
</style>
