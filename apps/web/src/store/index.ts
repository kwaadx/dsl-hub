/**
 * Store configuration
 *
 * This file sets up Pinia as the store management solution for the application.
 * It replaces the previous Vuex implementation.
 */

import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

// Create the Pinia instance
const pinia = createPinia()

// Add the persistedstate plugin to enable state persistence
pinia.use(piniaPluginPersistedstate)

export default pinia
