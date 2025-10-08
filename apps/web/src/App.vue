<script lang="ts" setup>
import {computed, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {useToast} from 'primevue/usetoast';
import {registerToast} from '@/lib/toast';

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import MainLayout from '@/layouts/MainLayout.vue'

const route = useRoute()
const layouts = {default: DefaultLayout, main: MainLayout} as const
const CurrentLayout = computed(() => {
  const key = (route.meta.layout ?? 'default') as keyof typeof layouts
  return layouts[key]
})

const toast = useToast()
onMounted(() => {
  registerToast(({ severity='info', summary, detail, life=4000 }) => {
    toast.add({ severity, summary, detail, life })
  })
})
</script>

<template>
  <Toast position="top-right"/>
  <component :is="CurrentLayout">
    <router-view/>
  </component>
</template>
