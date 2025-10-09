<script setup lang="ts">
import {ref, nextTick, onMounted} from 'vue'
import {useScroll, useEventListener} from '@vueuse/core'
import MessageRenderer from '@/components/thread/chat/MessageRenderer.vue'
import type {ChatMessage, UserMessage, AgentEvent} from '@/types/chat'
import {useThreadAgent} from '@/composables/useThreadAgent'
import {useI18n} from '@/composables/useI18n'

const {t} = useI18n()

const props = defineProps<{ flowId?: string; threadId?: string; token?: string }>()

const history = ref<ChatMessage[]>([])
const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || ''

const container = ref<HTMLElement | null>(null)
const {y} = useScroll(container, {behavior: 'smooth'})

function scrollToBottom() {
  nextTick(() => {
    const el = container.value
    if (!el) return
    y.value = el.scrollHeight
  })
}

const input = ref('')
const {sendToAgent, isBusy, mockBoot} = useThreadAgent({
  flowId: props.flowId,
  threadId: props.threadId ?? '',
  token: props.token,
  onAppend(msg) {
    const idx = history.value.findIndex(m => m.id === msg.id)
    if (idx >= 0) {
      history.value[idx] = msg
    } else {
      history.value.push(msg)
    }
    scrollToBottom()
  },
})

function send() {
  const text = input.value.trim()
  if (!text) return
  input.value = ''
  scrollToBottom()
  const userMsg: UserMessage = {
    id: crypto.randomUUID(),
    role: 'user',
    type: 'text',
    content: { text },
    ts: Date.now(),
  }
  // Do not push optimistically; rely on SSE message.created
  sendToAgent(userMsg)
}

useEventListener(window, 'keydown', (e: KeyboardEvent) => {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send()
})

if (history.value.length === 0) {
  mockBoot()
  nextTick(scrollToBottom)
}

onMounted(async () => {
  if (props.threadId) {
    try {
      const url = `${apiBase}/threads/${props.threadId}/messages`
      const headers = props.token ? { Authorization: `Bearer ${props.token}` } : {}
      const res = await fetch(url, { headers })
      const items = await res.json()
      const mapped: ChatMessage[] = Array.isArray(items)
        ? items.map((m: any) => {
            const id = m.id
            const role = m.role === 'user' ? 'user' : 'agent'
            const ts = Date.parse(m.created_at || '') || Date.now()
            if (m.format === 'json') {
              return { id, role, type: 'code', content: { language: 'json', code: JSON.stringify(m.content ?? {}, null, 2) }, ts } as ChatMessage
            }
            const text = m?.content?.text ?? (typeof m.content === 'string' ? m.content : '')
            return { id, role, type: 'text', content: { text }, ts } as ChatMessage
          })
        : []
      history.value = mapped
    } catch (e) {
      // ignore fetch errors for now
    }
  }
  scrollToBottom()
})
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
        :message="m"
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
        <Button label="Send" icon="pi pi-send" @click="send"
                :disabled="!input.trim()"/>
      </div>
    </div>
  </div>
</template>

