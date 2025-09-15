import App from './App.vue'
import store from './store'

import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'

import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import 'material-symbols/outlined.css'
import '@/assets/css/screen.scss'

import loader from 'vue3-ui-preloader'
import 'vue3-ui-preloader/dist/loader.css'
import VueDraggableResizable from 'vue-draggable-resizable'

import { setupI18n } from './i18n'
import router from './router'

import { le, ll, lw } from '@/utils/logger'
import 'vue-draggable-resizable/style.css'

import { registerSW } from 'virtual:pwa-register'
import { createApp } from 'vue'

if ('serviceWorker' in navigator) {
  registerSW({ immediate: true, type: 'module' })
}

window.ll = ll
window.lw = lw
window.le = le

const app = createApp(App)

app.use(setupI18n())
app.use(store)
app.use(router)
app.use(PrimeVue)
app.use(ConfirmationService)
app.use(DialogService)
app.use(ToastService)

app.component('VueDraggableResizable', VueDraggableResizable)
app.component('UIPreloader', loader)

app.mount('#app')
