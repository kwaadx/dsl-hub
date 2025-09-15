<template>
  <Toast
    ref="serverToast"
    :pt="{
      container: { style: { 'backdrop-filter': 'none' } },
    }"
    group="server"
    position="center"
  >
    <template #container="{ message }">
      <section class="flex p-3 gap-3 w-full bg-black-alpha-90 border-round-xl">
        <i class="pi pi-exclamation-circle text-2xl"></i>
        <div class="flex flex-column gap-3 w-full">
          <p class="m-0 text-lg font-semibold">{{ message.summary }}</p>
          <p class="m-0 text-base">{{ message.detail }}</p>
        </div>
      </section>
    </template>
  </Toast>
  <ConfirmDialog />
  <RightDrawer />
  <StatsMonitor />
  <Workspace />
  <RosDialog />
</template>

<script setup>
  import { useIntervalFn } from '@vueuse/core'
  import { useToast } from 'primevue/usetoast'
  import { computed, onBeforeUnmount, onMounted } from 'vue'
  import { useStore } from 'vuex'

  import RightDrawer from '@/components/main/RightDrawer.vue'
  import RosDialog from '@/components/main/ROSDialog.vue'
  import StatsMonitor from '@/components/main/StatsMonitor.vue'
  import Workspace from '@/components/main/Workspace.vue'
  import { usePreloader } from '@/composables/preloader/usePreloader'
  import { useServerToast } from '@/composables/server/useServerToast'
  import { useKeys } from '@/composables/useKeys'

  const store = useStore()
  const preloader = usePreloader()

  const currentUser = computed(() => store.getters['user/current'])
  const authToken = computed(() => store.getters['auth/token'])

  useKeys()

  const toast = useToast()
  useServerToast(toast)

  const { pause, resume } = useIntervalFn(() => {
    store.dispatch('ros/fetchTime')
  }, 1000)

  onMounted(async () => {
    // Set up main preloader set with both API and ROS operations
    await preloader.addOperationSet('main', {
      api: [
        'refresh-token',
        'config',
        'dynamic-variables',
        'users/me',
        'workspaces',
        'screens',
        'pages',
        'widgets',
      ],
      ros: ['connect', 'fetchNodes', 'fetchTopics', 'fetchServices', 'fetchParamNames'],
      custom: [],
    })

    preloader.setActiveSet('main')

    try {
      // Track API operation
      await store.dispatch('user/fetchCurrent')
      preloader.addApiOperation('users/me')

      if (currentUser.value) {
        // Track ROS operations using the enhanced preloader
        await preloader.trackRosAction('connect', store.dispatch('ros/connect', authToken.value))

        await preloader.trackRosAction('fetchNodes', store.dispatch('ros/fetchNodes'))

        await preloader.trackRosAction('fetchTopics', store.dispatch('ros/fetchTopics'))

        await preloader.trackRosAction('fetchServices', store.dispatch('ros/fetchServices'))

        await preloader.trackRosAction('fetchParamNames', store.dispatch('ros/fetchParamNames'))

        // Preload topic metadata (this is additional, not tracked in preloader)
        for (const topic of store.getters['ros/topics']) {
          await store.dispatch('ros/preloadTopicMeta', topic)
        }

        resume()
      }
    } catch (error) {
      console.error('Error during component mounting:', error)
    }
  })

  onBeforeUnmount(() => {
    store.dispatch('ros/disconnect')
    pause()
  })
</script>

<style scoped></style>
