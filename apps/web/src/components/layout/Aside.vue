<script setup lang="ts">

</script>

<template>
  <aside
    class="h-full border-r bg-white/70 dark:bg-neutral-800/70 backdrop-blur-sm overflow-y-auto"
    aria-label="Sidebar navigation"
  >
    <div class="p-4 border-b">
      <h1 class="text-sm font-semibold">DSL Hub</h1>
      <p class="text-xs text-neutral-500">Active chats</p>
    </div>

    <!-- Search -->
    <div class="p-3 border-b">
      <InputText :placeholder="'Seearch...'"></InputText>
    </div>

    <!-- Chats list placeholder -->
    <nav class="p-2 space-y-1">
      <button class="w-full text-left px-3 py-2 rounded-md hover:bg-black/5 dark:hover:bg-white/10">
        Pipeline Agent — Alpha
      </button>
      <button class="w-full text-left px-3 py-2 rounded-md hover:bg-black/5 dark:hover:bg-white/10">
        ROS2 Sensors Group
      </button>
      <button class="w-full text-left px-3 py-2 rounded-md hover:bg-black/5 dark:hover:bg-white/10">
        Outreach — Appliance
      </button>
    </nav>
  </aside>
</template>

<style scoped>

</style>
