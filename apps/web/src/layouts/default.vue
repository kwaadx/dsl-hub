<template>
  <div class="h-screen w-full overflow-hidden bg-neutral-50 dark:bg-neutral-900">
    <div class="grid h-full grid-cols-[280px_1fr]">
      <Aside/>
      <div class="flex h-full flex-col">
        <Header/>
        <Main>
          <slot/>
        </Main>
        <Footer/>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Aside from "@/components/layout/Aside.vue";
import Header from "@/components/layout/Header.vue";
import Main from "@/components/layout/Main.vue";
import Footer from "@/components/layout/Footer.vue";
</script>
