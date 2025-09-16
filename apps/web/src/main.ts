import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createPersistedState} from 'pinia-plugin-persistedstate'

import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'

import 'primeicons/primeicons.css'
import '@/assets/css/tailwind.css'
import '@/assets/css/screen.scss'

import router from './router'
import App from './App.vue'
import {le, ll, lw} from '@/utils/logger'

const pinia = createPinia()

const storage: Storage | undefined =
  typeof window !== 'undefined' ? window.localStorage : undefined

pinia.use(
  createPersistedState({
    key: (id) => `dsl-hub-web-${id}`,
    storage,
  })
)

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  ripple: true,
})
app.use(ConfirmationService)
app.use(DialogService)
app.use(ToastService)

declare global {
  interface Window {
    ll: typeof ll
    lw: typeof lw
    le: typeof le
  }
}
if (typeof window !== 'undefined') {
  window.ll = ll
  window.lw = lw
  window.le = le
}

if (import.meta.env.DEV) {
  app.config.performance = true
}

router.isReady().then(() => {
  app.mount('#app')
})
