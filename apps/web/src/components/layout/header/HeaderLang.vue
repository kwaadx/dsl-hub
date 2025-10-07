<script lang="ts" setup>
import { computed, ref } from 'vue'
import TieredMenu from 'primevue/tieredmenu'
import { useI18n } from '@/composables/useI18n'
import type { I18nLocale } from '@/plugins/i18n'
import { flagMap } from '@/plugins/i18n'

const { locale, availableLocales, setLocale } = useI18n()

type LangOption = { code: I18nLocale; name: string; flag: string }

const localeNames: Record<I18nLocale, string> = {
  en: 'English',
  es: 'Español',
  fr: 'Français',
  de: 'Deutsch',
  'pt-BR': 'Português (Brasil)',
  it: 'Italiano',
  pl: 'Polski',
  uk: 'Українська',
  ar: 'العربية',
  'zh-CN': '简体中文',
  ja: '日本語',
  ko: '한국어',
  hi: 'हिन्दी',
}

const languages = computed<LangOption[]>(() => {
  const avail = (availableLocales.value?.length ? availableLocales.value : ['en', 'uk']) as I18nLocale[]
  return avail.map((code) => ({
    code,
    name: localeNames[code],
    flag: flagMap[code],
  }))
})

function onChangeLang(next: I18nLocale) {
  if (next !== locale.value) setLocale(next)
  menuRef.value?.hide()
}

const menuRef = ref()
const menuItems = computed(() =>
  languages.value.map((opt) => ({
    id: opt.code,
    label: opt.name,
    icon: `fi fi-${opt.flag}`,
    command: () => onChangeLang(opt.code),
  }))
)

function toggleMenu(event: MouseEvent) {
  menuRef.value?.toggle(event)
}
</script>

<template>
  <div
    class="h-8 w-8 inline-flex items-center justify-center rounded-md cursor-pointer bg-surface-100 dark:bg-white"
    role="button"
    aria-label="Change language"
    @click="toggleMenu"
  >
    <span :class="['fi', `fi-${flagMap[locale as I18nLocale]}`]" />
  </div>

  <TieredMenu
    ref="menuRef"
    :model="menuItems"
    popup
    appendTo="body"
  />
</template>
