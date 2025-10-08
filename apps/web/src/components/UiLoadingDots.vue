<script setup lang="ts">
import {computed} from 'vue'

const props = withDefaults(defineProps<{
  size?: number | string
  color?: string
  gap?: number | string
  durationMs?: number
}>(), {
  size: 10,
  color: 'currentColor',
  gap: 12,
  durationMs: 1200,
})

const dotStyle = computed(() => ({
  width: typeof props.size === 'number' ? `${props.size}px` : String(props.size),
  height: typeof props.size === 'number' ? `${props.size}px` : String(props.size),
  backgroundColor: props.color,
  animationDuration: `${props.durationMs}ms`,
}))

const gapStyle = computed(() => ({
  columnGap: typeof props.gap === 'number' ? `${props.gap}px` : String(props.gap),
}))
</script>

<template>
  <div class="inline-flex items-center" :style="gapStyle">
    <span class="ui-dot" :style="{...dotStyle, animationDelay: '-0.28s'}" />
    <span class="ui-dot" :style="{...dotStyle, animationDelay: '-0.14s'}" />
    <span class="ui-dot" :style="dotStyle" />
  </div>
</template>

<style scoped>
@keyframes ui-dot-bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.6;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.ui-dot {
  display: inline-block;
  border-radius: 9999px;
  animation-name: ui-dot-bounce;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
}
</style>
