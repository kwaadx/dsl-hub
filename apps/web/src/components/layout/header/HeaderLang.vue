<script lang="ts" setup>
import Select from 'primevue/select'
import {computed} from 'vue'
import {useI18n} from '@/composables/useI18n'
import type {I18nLocale} from '@/plugins/i18n'
import {flagMap} from '@/plugins/i18n'

const {locale, availableLocales, setLocale} = useI18n()

type LangOption = { code: I18nLocale; name: string; flag: string }

const localeNames: Record<I18nLocale, string> = {
  en: 'English',
  uk: 'Українська',
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
}
</script>

<template>
  <Select
    v-model="locale"
    :options="languages"
    optionLabel="name"
    optionValue="code"
    class="h-10"
    @update:modelValue="onChangeLang"
  >
    <template #value="{ value }">
      <span v-if="value" class="inline-flex items-center gap-2">
        <span :class="['fi', `fi-${flagMap[value as I18nLocale]}`]"/>
      </span>
    </template>

    <template #option="{ option }">
      <span class="inline-flex items-center gap-2">
        <span :class="['fi', `fi-${option.flag}`]"/>
        <span>{{ option.name }}</span>
      </span>
    </template>
  </Select>
</template>
