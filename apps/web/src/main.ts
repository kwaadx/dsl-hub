import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'

import {useTheme, definePreset} from '@primevue/themes'
import Aura from '@primevue/themes/aura'

import 'primeicons/primeicons.css'
import '@/assets/css/tailwind.css'
import '@/assets/css/screen.scss'

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

app.use(PrimeVue, {
  ripple: true,
})
app.use(ConfirmationService)
app.use(DialogService)
app.use(ToastService)

app.use(pinia)
app.use(router)

await router.isReady()
app.mount('#app')
