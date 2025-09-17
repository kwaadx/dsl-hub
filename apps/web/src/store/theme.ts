import {defineStore} from 'pinia'
import {useDark, useToggle} from '@vueuse/core'

export const useThemeStore = defineStore('theme', {
  state: () => {
    const isDark = useDark({
      selector: 'html',
      attribute: 'class',
      valueDark: 'dark',
      valueLight: '',
      storageKey: 'theme:dark',
    })

    const toggleFn = useToggle(isDark)

    return {
      isDark,
      toggleFn
    }
  },
  actions: {
    toggleDark() {
      this.toggleFn()
    }
  },
  persist: true
})
