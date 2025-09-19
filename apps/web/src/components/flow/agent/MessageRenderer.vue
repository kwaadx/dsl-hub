<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage, AgentEvent } from './types'
import MsgText from '@/components/flow/agent/msg/MsgText.vue'
import MsgActions from '@/components/flow/agent/msg/MsgActions.vue'
import MsgChoice from '@/components/flow/agent/msg/MsgChoice.vue'
import MsgCard from '@/components/flow/agent/msg/MsgCard.vue'
import MsgNotice from '@/components/flow/agent/msg/MsgNotice.vue'
import MsgCode from '@/components/flow/agent/msg/MsgCode.vue'

const props = defineProps<{
  msg: ChatMessage
}>()

const emit = defineEmits<{
  (e: 'act', ev: AgentEvent): void
}>()

const side = computed(() => (props.msg.role === 'user' ? 'end' : 'start'))
const bubbleBase = 'max-w-[80%] rounded-2xl px-3 py-2 text-sm'
const bubbleByRole = computed(() =>
  props.msg.role === 'user'
    ? 'bg-indigo-600 text-white rounded-br-md'
    : 'bg-neutral-100 text-neutral-900 rounded-bl-md dark:bg-neutral-800 dark:text-neutral-100'
)
</script>

<template>
  <div class="flex" :class="side === 'end' ? 'justify-end' : 'justify-start'">
    <div v-if="msg.type === 'text'" :class="[bubbleBase, bubbleByRole]">
      <MsgText :text="msg.content.text" />
    </div>

    <div v-else-if="msg.type === 'actions'" class="w-full max-w-[80%]">
      <MsgActions :actions="msg.content.actions" @act="(a) => emit('act', a)" />
    </div>

    <div v-else-if="msg.type === 'choice'" class="w-full max-w-[80%]">
      <MsgChoice
        :label="msg.content.label"
        :options="msg.content.options"
        :kind="msg.content.kind"
        :name="msg.id"
        @submit="(payload) => emit('act', { kind: 'choice.submit', msgId: msg.id, payload })"
      />
    </div>

    <div v-else-if="msg.type === 'card'" class="w-full max-w-[80%]">
      <MsgCard :card="msg.content" @open="(url)=>emit('act', {kind:'card.open', url, msgId: msg.id})" />
    </div>

    <div v-else-if="msg.type === 'notice'" :class="[bubbleBase, bubbleByRole]">
      <MsgNotice :severity="msg.content.severity" :text="msg.content.text" />
    </div>

    <div v-else-if="msg.type === 'code'" class="w-full max-w-[80%]">
      <MsgCode :language="msg.content.language" :code="msg.content.code" />
    </div>

    <div v-else class="max-w-[80%] rounded-md border border-dashed p-2 text-xs opacity-70">
      Unsupported message type: {{ msg.type }}
    </div>
  </div>
</template>
