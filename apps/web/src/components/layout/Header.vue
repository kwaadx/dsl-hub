<script lang="ts" setup>
import HeaderTheme from "@/components/layout/header/HeaderTheme.vue";
import HeaderLang from "@/components/layout/header/HeaderLang.vue";
</script>

<template>
  <header class="flex items-center p-3 bg-white/10 dark:bg-neutral-800/70">
    <div class="flex items-center ml-auto h-10 gap-3">
      <HeaderTheme/>
      <HeaderLang/>
    </div>
  </header>
</template>
