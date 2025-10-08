<script lang="ts" setup>
import {computed} from 'vue'
import type {AgentEvent, ChatMessage} from '@/types/chat'
import MessageText from '@/components/thread/chat/message/MessageText.vue'
import MessageActions from '@/components/thread/chat/message/MessageActions.vue'
import MessageChoice from '@/components/thread/chat/message/MessageChoice.vue'
import MessageCard from '@/components/thread/chat/message/MessageCard.vue'
import MessageNotice from '@/components/thread/chat/message/MessageNotice.vue'
import MessageCode from '@/components/thread/chat/message/MessageCode.vue'

const props = defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  (e: 'act', ev: AgentEvent): void
}>()

const side = computed(() => (props.message.role === 'user' ? 'end' : 'start'))
const bubbleBase = 'max-w-[80%] rounded-2xl px-3 py-2 text-sm'
const bubbleByRole = computed(() =>
  props.message.role === 'user'
    ? 'bg-indigo-600 text-white rounded-br-md'
    : 'bg-neutral-100 text-neutral-900 rounded-bl-md dark:bg-neutral-800 dark:text-neutral-100'
)
</script>

<template>
  <div :class="side === 'end' ? 'justify-end' : 'justify-start'" class="flex">
    <div v-if="message.type === 'text'" :class="[bubbleBase, bubbleByRole]">
      <MessageText :text="message.content.text"/>
    </div>

    <div v-else-if="message.type === 'actions'" class="w-full max-w-[80%]">
      <MessageActions :actions="message.content.actions" @act="(a) => emit('act', a)"/>
    </div>

    <div v-else-if="message.type === 'choice'" class="w-full max-w-[80%]">
      <MessageChoice
        :kind="message.content.kind"
        :label="message.content.label"
        :name="message.id"
        :options="message.content.options"
        @submit="(payload) => emit('act', { kind: 'choice.submit', msgId: message.id, payload })"
      />
    </div>

    <div v-else-if="message.type === 'card'" class="w-full max-w-[80%]">
      <MessageCard :card="message.content"
               @open="(url)=>emit('act', {kind:'card.open', url, msgId: message.id})"/>
    </div>

    <div v-else-if="message.type === 'notice'" :class="[bubbleBase, bubbleByRole]">
      <MessageNotice :severity="message.content.severity" :text="message.content.text"/>
    </div>

    <div v-else-if="message.type === 'code'" class="w-full max-w-[80%]">
      <MessageCode :code="message.content.code" :language="message.content.language"/>
    </div>

    <div v-else class="max-w-[80%] rounded-md border border-dashed p-2 text-xs opacity-70">
      Unsupported message type: {{ message.type }}
    </div>
  </div>
</template>
