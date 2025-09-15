import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

export const AuraPreset = definePreset(Aura, {
  semantic: {
    colorScheme: {
      light: {},
      dark: {},
    },
  },
})
