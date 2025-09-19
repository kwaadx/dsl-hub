<script setup lang="ts">
import {computed} from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
const model = computed({
  get: () => props.modelValue,
  set: (v: string) => emit('update:modelValue', v),
})
</script>

<template>
  <div class="px-3 mb-2">
    <IconField iconPosition="right" class="w-full">
      <InputText v-model="model" class="w-full pr-9" placeholder="Search..."/>
      <InputIcon
        v-if="model"
        class="pi pi-times cursor-pointer"
        @click="model = ''"
        aria-label="Clear"
      />
    </IconField>
  </div>
</template>
