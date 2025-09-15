import { createI18n } from 'vue-i18n'

export function setupI18n(
  options = { locale: import.meta.env.VITE_APP_I18N_LOCALE, legacy: false }
) {
  const i18n = createI18n({
    ...options,
    messages: loadLocaleMessages(),
  })

  setI18nLanguage(i18n, options.locale)

  return i18n
}

export function setI18nLanguage(i18n, locale) {
  i18n.global.locale.value = locale
  document.querySelector('html').setAttribute('lang', locale)
}

function loadLocaleMessages() {
  const locales = import.meta.glob('./locales/*.json', { eager: true })
  const additionalLocales = import.meta.glob('./locales/*.content.js', { eager: true })
  const messages = {}

  for (const path in locales) {
    const locale = path.match(/\/locales\/(.*)\.json$/)[1]
    messages[locale] = locales[path].default || locales[path]
  }

  for (const path in additionalLocales) {
    const locale = path.match(/\/locales\/(.*)\.content\.js$/)[1]
    if (!messages[locale]) {
      messages[locale] = {}
    }
    messages[locale].content = additionalLocales[path].default || additionalLocales[path]
  }

  return messages
}
