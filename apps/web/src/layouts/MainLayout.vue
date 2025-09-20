<script setup lang="ts">
import {useLayoutStore} from '@/store/layout'
import Aside from '@/components/layout/Aside.vue'
import Header from '@/components/layout/Header.vue'
import Main from '@/components/layout/Main.vue'
import Footer from '@/components/layout/Footer.vue'

const layoutStore = useLayoutStore()
</script>

<template>
  <div class="h-dvh w-full bg-neutral-50 dark:bg-neutral-900">
    <div
      class="grid h-full min-h-0 transition-all duration-300 !grid-cols-1"
      :class="layoutStore.sidebarVisible ? 'md:!grid-cols-[280px_1fr]' : 'md:!grid-cols-[0px_1fr]'"
    >
      <Aside/>

      <div class="flex min-h-0 flex-col">
        <Header/>

        <Main class="flex-1 min-h-0 overflow-hidden">
          <slot/>
        </Main>

        <Footer/>
      </div>
    </div>

    <div v-if="!layoutStore.sidebarVisible" class="absolute left-3 top-4 z-40">
      <i class="pi pi-bars !text-2xl cursor-pointer" @click="layoutStore.toggleSidebar"/>
    </div>

    <div
      v-if="layoutStore.sidebarVisible"
      class="fixed inset-0 z-40 bg-black/50 md:hidden"
      @click="layoutStore.toggleSidebar"
    />
  </div>
</template>
