<script lang="ts" setup>
import {computed} from 'vue'
import {useRoute} from 'vue-router'
import {useLayoutStore} from "@/store/layout";

const route = useRoute()
const layoutStore = useLayoutStore();

interface CrumbItem {
  label: string
  to?: any
  icon?: string
  disabled?: boolean
}

const home = computed<CrumbItem>(() => ({
  icon: 'pi pi-home',
  to: {name: 'Home'},
  label: 'Home',
}))

const items = computed<CrumbItem[]>(() => {
  const matched = route.matched.filter(r => r.meta && (r.meta as any).breadcrumb)

  const mapped = matched
    .filter(r => r.name !== 'Home')
    .map((r) => {
      const raw = (r.meta as any).breadcrumb
      const label = typeof raw === 'function' ? raw(route) : raw
      return {
        label: String(label ?? r.name ?? ''),
        to: {name: r.name as string, params: route.params},
      } as CrumbItem
    })

  if (mapped.length > 0) {
    mapped[mapped.length - 1].disabled = true
    mapped[mapped.length - 1].to = undefined
  }

  return mapped
})
</script>

<template>
  <Breadcrumb
    :home="home"
    :model="items"
    class="max-w-full overflow-hidden text-sm !bg-transparent !p-0"
    :class="[
      layoutStore.sidebarVisible ? 'md:ml-0' : '',
      '!transition-all z-10 ml-10'
    ]"
  >
    <template #item="{ item }">
      <RouterLink
        v-if="!item.disabled && item.to"
        :to="item.to"
        class="text-primary-600 hover:underline inline-flex items-center gap-2 max-w-[220px]"
      >
        <i v-if="item.icon" :class="item.icon" aria-hidden="true"></i>
        <span class="truncate">{{ item.label }}</span>
      </RouterLink>

      <span v-else class="text-muted-color inline-flex items-center gap-2 max-w-[260px]">
        <i v-if="item.icon" :class="item.icon" aria-hidden="true"></i>
        <span class="truncate">{{ item.label }}</span>
      </span>
    </template>

    <template #separator>
      <span class="mx-2 text-muted-color">/</span>
    </template>
  </Breadcrumb>
</template>
