import { createI18n, type DefineLocaleMessage } from 'vue-i18n'
import en from '@/locales/en.json'

export type I18nLocale = 'en' | 'uk'
export const flagMap: Record<I18nLocale, string> = {
  en: 'us',
  uk: 'ua',
}
export const SUPPORTED_LOCALES: readonly I18nLocale[] = ['en', 'uk'] as const
const FALLBACK_LOCALE: I18nLocale = 'en'

function normalizeLocale(input?: string | null): I18nLocale {
  const raw = (input ?? '').toLowerCase()
  const short = (raw.split('-')[0] || '') as I18nLocale
  return (SUPPORTED_LOCALES.includes(short) ? short : FALLBACK_LOCALE) as I18nLocale
}

const stored = normalizeLocale(localStorage.getItem('locale'))
const browser = normalizeLocale(navigator.language)
const initialLocale: I18nLocale = stored || browser || FALLBACK_LOCALE

const messages: Record<I18nLocale, DefineLocaleMessage> = {
  en,
  uk: {},
}

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: FALLBACK_LOCALE,
  messages,
})

function applyDocumentLang(lang: I18nLocale) {
  try {
    document.documentElement.setAttribute('lang', lang)
  } catch {}
}

export async function loadLocale(lang: I18nLocale) {
  const current = i18n.global.locale.value as I18nLocale
  if (current === lang && Object.keys(i18n.global.getLocaleMessage(lang) ?? {}).length > 0) {
    applyDocumentLang(lang)
    return
  }

  if (!i18n.global.availableLocales.includes(lang)) {
    i18n.global.setLocaleMessage(lang, {})
  }

  if (Object.keys(i18n.global.getLocaleMessage(lang) ?? {}).length === 0) {
    const m = await import(`@/locales/${lang}.json`).then(m => m.default)
    i18n.global.setLocaleMessage(lang, m as DefineLocaleMessage)
  }

  i18n.global.locale.value = lang
  localStorage.setItem('locale', lang)
  applyDocumentLang(lang)
}

applyDocumentLang(initialLocale)
