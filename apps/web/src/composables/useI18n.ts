import { useI18n as useVueI18n } from 'vue-i18n'
import { computed } from 'vue'

/**
 * Enhanced useI18n composable that provides additional utilities
 * for working with translations in the Composition API
 *
 * @returns Enhanced i18n utilities
 */
export function useI18n() {
  const i18n = useVueI18n()

  /**
   * Get a translation with automatic type inference
   * Keeps the same signature as the original `i18n.t`
   */
  const t = (...args: Parameters<typeof i18n.t>): ReturnType<typeof i18n.t> => {
    return i18n.t(...args)
  }

  /**
   * Get the current locale
   */
  const locale = computed({
    get: () => i18n.locale.value,
    set: (value: string) => {
      i18n.locale.value = value
    }
  })

  /**
   * Get all available locales
   */
  const availableLocales = computed(() => i18n.availableLocales)

  /**
   * Check if a translation exists
   * @param key - The translation key to check
   * @returns True if the translation exists
   */
  const exists = (key: string) => {
    return i18n.te(key)
  }

  return {
    ...i18n,
    t,
    locale,
    availableLocales,
    exists
  }
}
