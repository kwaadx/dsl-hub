<template>
  <Toast ref="globalToast" />
  <Toast ref="commonErrorToast" />
  <UIPreloader
    v-show="isLoading"
    :disable-scrolling="true"
    class="z-preloader absolute"
    color1="#cccccc"
    color2="#17fd3d"
    name="circular"
    object="#ff9633"
    opacity="100"
    size="5"
    speed="2"
  />
  <component :is="layoutComponent" />
</template>

<script setup>
  import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useStore } from 'vuex'

  import { usePreloader } from '@/composables/preloader/usePreloader'
  import { useDocumentFontSize } from '@/composables/screen/useDocumentFontSize'
  import { useNavigatorWakeLock } from '@/composables/screen/useNavigatorWakeLock'
  import { useThemeSwitcher } from '@/composables/screen/useThemeSwitcher'
  import { useCommonErrorToast } from '@/composables/useCommonErrorToast'
  import { useGlobalToast } from '@/composables/useGlobalToast'
  import { useOfflineEndpoints } from '@/composables/useOfflineEndpoints'
  import { useRefreshToken } from '@/composables/useRefreshToken'
  import { setupTooltipCleaner } from '@/utils/tooltipCleaner'

  const { init, syncWithSW, setEndpoints } = useOfflineEndpoints()
  init()

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const preloader = usePreloader()

  const layoutComponent = computed(() => route.meta.layout)
  const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
  const configScreenDefaults = computed(() => store.getters['config']?.screen?.defaults)

  const globalToast = ref(null)
  const commonErrorToast = ref(null)
  const isLoading = ref(false)

  useGlobalToast(globalToast)
  useCommonErrorToast(commonErrorToast)
  useRefreshToken()
  useDocumentFontSize()
  useThemeSwitcher()
  useNavigatorWakeLock()
  setupTooltipCleaner()

  watch(
    isAuthenticated,
    (newValue, oldValue) => {
      if (!newValue && oldValue) {
        store.commit('widget/resetActive')
        store.commit('widget/resetCurrent')
        store.commit('widget/resetWidgets')

        store.commit('page/resetCurrent')
        store.commit('page/resetPages')

        store.commit('screen/resetCurrent')
        store.commit('screen/resetScreens')

        store.commit('workspace/resetCurrent')
        store.commit('workspace/resetWorkspaces')

        preloader.resetActiveSet()

        router.push('/login')
      }

      if (!oldValue && newValue) {
        preloader.setActiveSet('afterLogin')
      }
    },
    { immediate: true }
  )

  watch(
    () => preloader.isActiveSetCompleted.value,
    (isCompleted) => {
      if (isCompleted && preloader.activeSetName.value) {
        // All operations completed, reset the active set
        preloader.resetActiveSet()
      }
    },
    { immediate: true }
  )

  watch(
    () => preloader.activeSetName.value,
    (newValue) => {
      isLoading.value = newValue !== null
    },
    { immediate: true }
  )

  const handleError = (event) => {
    const error = event.error
    const errorMessage = error.message || 'Unknown error'
    const errorStack = error.stack
      ? error.stack.split('\n').slice(0, 3).join('\n')
      : 'Stack trace not available'
    const formattedError = `
    An error occurred: ${errorMessage}
    Source: ${event.filename} at line ${event.lineno}, column ${event.colno}
    Stack trace:
    ${errorStack}
  `

    store.commit('showToast', {
      severity: 'error',
      summary: '[ERROR]',
      detail: formattedError,
      life: null,
    })
  }

  onMounted(async () => {
    await syncWithSW()
    await setEndpoints([
      'https://localhost',
      'https://192.168.1.114',
      'https://prime-carefully-shark.ngrok-free.app',
    ])

    await store.dispatch('fetchConfig')
    store.commit('screen/setDefault', configScreenDefaults.value)
    window.addEventListener('error', handleError)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('error', handleError)
  })
</script>

<style scoped></style>
