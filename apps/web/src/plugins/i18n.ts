import { createI18n, type DefineLocaleMessage } from 'vue-i18n'
import en from '@/locales/en.json'
import es from '@/locales/es.json'
import fr from '@/locales/fr.json'
import de from '@/locales/de.json'
import ptBR from '@/locales/pt-BR.json'
import it from '@/locales/it.json'
import pl from '@/locales/pl.json'
import uk from '@/locales/uk.json'
import ar from '@/locales/ar.json'
import zhCN from '@/locales/zh-CN.json'
import ja from '@/locales/ja.json'
import ko from '@/locales/ko.json'
import hi from '@/locales/hi.json'

export type I18nLocale =
  | 'en'
  | 'es'
  | 'fr'
  | 'de'
  | 'pt-BR'
  | 'it'
  | 'pl'
  | 'uk'
  | 'ar'
  | 'zh-CN'
  | 'ja'
  | 'ko'
  | 'hi'

export const flagMap: Record<I18nLocale, string> = {
  en: 'us',
  es: 'es',
  fr: 'fr',
  de: 'de',
  'pt-BR': 'br',
  it: 'it',
  pl: 'pl',
  uk: 'ua',
  ar: 'sa',
  'zh-CN': 'cn',
  ja: 'jp',
  ko: 'kr',
  hi: 'in',
}

export const SUPPORTED_LOCALES: readonly I18nLocale[] = [
  'en',
  'es',
  'fr',
  'de',
  'pt-BR',
  'it',
  'pl',
  'uk',
  'ar',
  'zh-CN',
  'ja',
  'ko',
  'hi',
] as const

const FALLBACK_LOCALE: I18nLocale = 'en'

function normalizeLocale(input?: string | null): I18nLocale {
  const raw = (input ?? '').toLowerCase()
  // Map lowercase inputs to canonical codes used in SUPPORTED_LOCALES
  const CANONICAL: Record<string, I18nLocale> = {
    'en': 'en',
    'es': 'es',
    'fr': 'fr',
    'de': 'de',
    'pt-br': 'pt-BR',
    'it': 'it',
    'pl': 'pl',
    'uk': 'uk',
    'ar': 'ar',
    'zh-cn': 'zh-CN',
    'ja': 'ja',
    'ko': 'ko',
    'hi': 'hi',
  }
  if (raw in CANONICAL) return CANONICAL[raw]
  const short = raw.split('-')[0]
  return (CANONICAL[short] ?? FALLBACK_LOCALE) as I18nLocale
}

const stored = normalizeLocale(localStorage.getItem('locale'))
const browser = normalizeLocale(navigator.language)
const initialLocale: I18nLocale = stored || browser || FALLBACK_LOCALE

const messages: Partial<Record<I18nLocale, DefineLocaleMessage>> = {
  en,
  es,
  fr,
  de,
  'pt-BR': ptBR,
  it,
  pl,
  uk,
  ar,
  'zh-CN': zhCN,
  ja,
  ko,
  hi,
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
