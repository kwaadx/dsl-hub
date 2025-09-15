import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'
import type { ThemePreset } from '@primevue/themes'

/**
 * Custom Aura theme preset for the application
 *
 * This preset extends the default Aura theme from PrimeVue with custom
 * configuration for light and dark color schemes.
 *
 * @see https://primevue.org/theming/
 */
export const AuraPreset: ThemePreset = definePreset(Aura, {
  semantic: {
    // Color scheme configuration for light and dark modes
    colorScheme: {
      light: {
        // Light mode specific overrides can be added here
      },
      dark: {
        // Dark mode specific overrides can be added here
      },
    },
  },
})
