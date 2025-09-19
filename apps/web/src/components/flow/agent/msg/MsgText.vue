<script setup lang="ts">
defineProps<{ text: string }>()
</script>

<template>
  <div class="whitespace-pre-line leading-relaxed">
    {{ text }}
  </div>
</template>
