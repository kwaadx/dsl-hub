<script setup lang="ts">
import {computed} from 'vue'
import {useRoute} from 'vue-router'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import MainLayout from '@/layouts/MainLayout.vue'

const route = useRoute()
const layouts = {default: DefaultLayout, main: MainLayout} as const
const CurrentLayout = computed(() => {
  const key = (route.meta.layout ?? 'default') as keyof typeof layouts
  return layouts[key]
})
</script>

<template>
  <Toast/>
  <component :is="CurrentLayout">
    <router-view/>
  </component>
</template>
