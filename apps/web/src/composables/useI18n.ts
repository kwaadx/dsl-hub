import {computed} from 'vue'
import {useI18n as useVueI18n, type Composer} from 'vue-i18n'
import {loadLocale, type I18nLocale, SUPPORTED_LOCALES} from '@/plugins/i18n'

export function useI18n() {
  const composer = useVueI18n()
  const t: Composer['t'] = composer.t

  const locale = computed<I18nLocale>({
    get: () => composer.locale.value as I18nLocale,
    set: (val) => {
      void setLocale(val)
    },
  })

  const availableLocales = computed<I18nLocale[]>(() =>
    SUPPORTED_LOCALES.filter(l => composer.availableLocales.includes(l)) as I18nLocale[]
  )

  const exists = (key: string, loc?: I18nLocale) =>
    composer.te(key, (loc ?? composer.locale.value) as I18nLocale)

  async function setLocale(lang: I18nLocale) {
    await loadLocale(lang)
  }

  return {
    ...composer,
    t,
    locale,
    availableLocales,
    exists,
    setLocale,
  }
}
