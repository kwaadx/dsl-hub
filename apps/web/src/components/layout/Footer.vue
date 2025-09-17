<script setup lang="ts">
import {ref} from 'vue';

const year = ref(new Date().getFullYear());
</script>

<template>
  <footer
    class="bg-white dark:bg-neutral-800 flex justify-center text-xs text-neutral-500 w-full p-3">
    © {{ year }} DSL Hub
  </footer>
</template>

<style scoped>

</style>
