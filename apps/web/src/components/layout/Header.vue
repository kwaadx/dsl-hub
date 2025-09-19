<script setup lang="ts">
import HeaderMode from "@/components/layout/header/HeaderMode.vue";
import HeaderTheme from "@/components/layout/header/HeaderTheme.vue";
</script>

<template>
  <header class="flex items-center p-3 bg-white/10 dark:bg-neutral-800/70">
    <HeaderMode/>
    <div class="flex items-center ml-auto h-10">
      <HeaderTheme/>
    </div>
  </header>
</template>
