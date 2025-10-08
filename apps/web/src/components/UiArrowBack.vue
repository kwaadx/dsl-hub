<script setup lang="ts">
import {useRouter} from "vue-router";

const router = useRouter()
</script>

<template>
  <Button
    @click="router.back()"
    class="!p-0"
    icon="pi pi-arrow-left"
    link
  />
</template>
