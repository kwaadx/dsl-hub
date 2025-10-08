<script lang="ts" setup>
import {ref} from 'vue'

const props = withDefaults(defineProps<{
  label: string
  options: Array<{ label: string; value: string }>
  kind?: 'dropdown' | 'radio'
  name?: string
}>(), {kind: 'dropdown'})

const emit = defineEmits<{
  (e: 'submit', payload: { value: string }): void
}>()

const value = ref<string | null>(null)

function submit() {
  if (value.value) emit('submit', {value: value.value})
}
</script>

<template>
  <div class="rounded-2xl bg-neutral-100 p-3 dark:bg-neutral-800">
    <div class="mb-2 text-sm font-medium opacity-80">{{ label }}</div>

    <div v-if="kind === 'dropdown'" class="flex items-center gap-2">
      <Select v-model="value" :options="options" class="min-w-56" optionLabel="label"
              optionValue="value"/>
      <Button :disabled="!value" label="OK" size="small" @click="submit"/>
    </div>

    <div v-else class="flex flex-col gap-2">
      <label
        v-for="opt in options"
        :key="opt.value"
        class="flex cursor-pointer items-center gap-2"
      >
        <RadioButton v-model="value" :inputId="`${name}-${opt.value}`" :value="opt.value"
                     name="choice"/>
        <span>{{ opt.label }}</span>
      </label>
      <div class="pt-1">
        <Button :disabled="!value" label="Confirm" size="small" @click="submit"/>
      </div>
    </div>
  </div>
</template>
