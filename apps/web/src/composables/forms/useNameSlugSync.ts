import {ref, computed, watch, type Ref} from 'vue'

/**
 * Keeps a slug field in sync with a name field until the user edits the slug manually.
 * Also provides validation helpers and a reusable slugify implementation.
 */
export function useNameSlugSync(name: Ref<string>) {
  const slug = ref('')
  const slugEdited = ref(false)

  // Allowed: lowercase letters, digits and single dashes between segments
  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

  function slugify(input: string) {
    return (input || '')
      .toLowerCase()
      .trim()
      .replace(/['"]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
  }

  const slugValid = computed(() => !slug.value || slugPattern.test(slug.value))

  // Auto-generate slug from name until user edits the slug manually
  watch(name, (v) => {
    if (!slugEdited.value) slug.value = slugify(v || '')
  })

  function onSlugInput() {
    slugEdited.value = true
  }

  return {slug, slugEdited, slugPattern, slugValid, slugify, onSlugInput}
}
