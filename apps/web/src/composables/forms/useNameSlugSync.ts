import {ref, computed, watch, type Ref} from 'vue'
import {slugify} from '@/utils/slugify'

export function useNameSlugSync(name: Ref<string>) {
  const slug = ref('')
  const slugEdited = ref(false)
  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
  const slugValid = computed(() => !slug.value || slugPattern.test(slug.value))

  watch(name, (v) => {
    if (!slugEdited.value) slug.value = slugify(v || '')
  })

  function onSlugInput() {
    slugEdited.value = true
  }

  return {slug, slugEdited, slugPattern, slugValid, slugify, onSlugInput}
}
