<script setup lang="ts">
import {ref, nextTick, computed} from 'vue'
import {useScroll, useStorage, useEventListener} from '@vueuse/core'
import MessageRenderer from '@/components/flow/agent/MessageRenderer.vue'
import type {ChatMessage, UserMessage, AgentEvent} from '@/components/flow/agent/types'
import {useAgentFlow} from '@/composables/useAgentFlow'
import { useI18n } from '@/composables/useI18n'

const { t } = useI18n()

const props = defineProps<{ flowId?: string }>()

const storageKey = computed(() => `chatflow:${props.flowId ?? 'demo'}`)
const history = useStorage<ChatMessage[]>(storageKey.value, [], localStorage, {
  serializer: {
    read: (v) => (v ? JSON.parse(v) : []),
    write: (v) => JSON.stringify(v),
  },
})

const container = ref<HTMLElement | null>(null)
const {scrollTo} = useScroll(container)

function scrollToBottom() {
  nextTick(() => {
    const el = container.value
    if (!el) return
    scrollTo({top: el.scrollHeight, behavior: 'smooth'})
  })
}

const input = ref('')
const {sendToAgent, isBusy, mockBoot} = useAgentFlow({
  onAppend(msg) {
    history.value.push(msg)
    scrollToBottom()
  },
})

function send() {
  const text = input.value.trim()
  if (!text) return
  const userMsg: UserMessage = {
    id: crypto.randomUUID(),
    role: 'user',
    type: 'text',
    content: {text},
    ts: Date.now(),
  }
  history.value.push(userMsg)
  input.value = ''
  scrollToBottom()
  sendToAgent(userMsg)
}

useEventListener(window, 'keydown', (e: KeyboardEvent) => {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
})

if (history.value.length === 0) {
  mockBoot()
  nextTick(scrollToBottom)
}
</script>

<template>
  <div
    class="flex flex-1 h-full w-full min-w-0 min-h-0 flex-col rounded-2xl border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
    <div
      class="shrink-0 flex items-center gap-3 border-b border-neutral-200 px-4 py-3 dark:border-neutral-800">
      <i class="pi pi-comments text-lg"></i>
      <div class="font-medium">Agent chat</div>
      <div class="ml-auto">
        <ProgressSpinner v-if="isBusy" style="width:18px;height:18px" strokeWidth="6"/>
      </div>
    </div>

    <div
      ref="container"
      class="grow min-h-0 overflow-y-auto overscroll-contain p-3 space-y-2"
    >
      <MessageRenderer
        v-for="m in history"
        :key="m.id"
        :msg="m"
        @act="(ev) => sendToAgent(ev as AgentEvent)"
      />

      <div v-if="isBusy" class="flex justify-start">
        <div
          class="max-w-[75%] rounded-2xl rounded-bl-md bg-neutral-100 px-3 py-2 text-sm text-neutral-800 dark:bg-neutral-800 dark:text-neutral-100">
          <div class="flex items-center gap-2">
            <ProgressSpinner style="width:16px;height:16px" strokeWidth="6"/>
            Думаю...
          </div>
        </div>
      </div>
    </div>

    <div
      class="shrink-0 border-t border-neutral-200 p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] dark:border-neutral-800">
      <div class="flex items-center gap-2">
        <InputText
          v-model="input"
          class="w-full"
          placeholder="Напишіть повідомлення… (Ctrl/⌘ + Enter — надіслати)"
          @keyup.enter="send"
        />
        <Button :label="t('button.send')" icon="pi pi-send" @click="send" :disabled="!input.trim()"/>
      </div>
    </div>
  </div>
</template>

