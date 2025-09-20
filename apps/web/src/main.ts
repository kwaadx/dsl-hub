import { createApp } from 'vue'

import { VueQueryPlugin } from '@tanstack/vue-query'
import { queryClient } from '@/core/query'
import { i18n } from '@/plugins/i18n'

import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'

import { definePreset, useTheme } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import 'flag-icons/css/flag-icons.min.css'
import 'primeicons/primeicons.css'
import '@/assets/css/tailwind.css'

import router from './router'
import pinia from './store'
import App from './App.vue'
import '@/utils/logger'

useTheme({
  preset: definePreset(Aura),
  options: {
    darkModeSelector: '.dark',
  },
})

const app = createApp(App)

if (import.meta.env.DEV) {
  app.config.performance = true
}

app.use(VueQueryPlugin, { queryClient })
app.use(PrimeVue, { ripple: true })
app.use(ConfirmationService)
app.use(DialogService)
app.use(ToastService)

app.use(i18n)
app.use(pinia)
app.use(router)

await router.isReady()
app.mount('#app')
