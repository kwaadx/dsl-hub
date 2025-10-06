<script lang="ts" setup>
import {computed} from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
const model = computed({
  get: () => props.modelValue,
  set: (v: string) => emit('update:modelValue', v),
})
</script>

<template>
  <div class="px-3">
    <IconField class="w-full" iconPosition="right">
      <InputText v-model="model" class="w-full pr-9" placeholder="Search..."/>
      <InputIcon
        v-if="model"
        aria-label="Clear"
        class="pi pi-times cursor-pointer"
        @click="model = ''"
      />
    </IconField>
  </div>
</template>
