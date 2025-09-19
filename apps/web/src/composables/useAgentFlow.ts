import {ref} from 'vue'
import type {AgentEvent, ChatMessage, UserMessage} from '@/components/flow/agent/types'

export function useAgentFlow(opts: {
  onAppend: (m: ChatMessage) => void
}) {
  const isBusy = ref(false)

  function append(m: ChatMessage) {
    opts.onAppend(m)
  }

  // тут ти підключиш SSE/WebSocket/HTTP
  async function sendToAgent(msg: UserMessage | AgentEvent) {
    isBusy.value = true

    // DEMO — імітуємо відповіді за типами евентів
    await sleep(500)

    // якщо це клік дії
    if ('kind' in msg && msg.kind === 'action.click') {
      append({
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'notice',
        content: {severity: 'success', text: `Action "${msg.actionId}" accepted`},
        ts: Date.now(),
      })
      isBusy.value = false
      return
    }

    // якщо це сабміт вибору
    if ('kind' in msg && msg.kind === 'choice.submit') {
      append({
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'text',
        content: {text: `You selected: ${msg.payload.value}`},
        ts: Date.now(),
      })
      isBusy.value = false
      return
    }

    // стандарт: агент відповідає і пропонує інтерактив
    const chunks: ChatMessage[] = [
      {
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'text',
        content: {text: 'Привіт! Я можу зробити кілька дій для твого flow.'},
        ts: Date.now(),
      },
      {
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'actions',
        content: {
          actions: [
            {id: 'run-validation', label: 'Run validation', icon: 'pi pi-check'},
            {id: 'show-preview', label: 'Show preview', icon: 'pi pi-eye', kind: 'secondary'},
            {id: 'delete-flow', label: 'Delete', icon: 'pi pi-trash', kind: 'danger'},
          ],
        },
        ts: Date.now(),
      },
      {
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'choice',
        content: {
          label: 'Оберіть середовище деплоя',
          kind: 'dropdown',
          options: [
            {label: 'Development', value: 'dev'},
            {label: 'Staging', value: 'stg'},
            {label: 'Production', value: 'prod'},
          ],
        },
        ts: Date.now(),
      },
      {
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'card',
        content: {
          title: 'Flow: Pump Controller',
          description: 'Ось короткий опис твого поточного flow.',
          image: 'https://picsum.photos/800/300',
          url: 'https://example.com/flow/123',
          meta: [
            {label: 'Version', value: 'v2.3.1'},
            {label: 'Status', value: 'OK'},
          ],
        },
        ts: Date.now(),
      },
      {
        id: crypto.randomUUID(),
        role: 'agent',
        type: 'code',
        content: {
          language: 'json',
          code: `{
  "id": "flow-123",
  "nodes": [
    {"id":"sensor.in","type":"mqtt","topic":"/pump/temp"},
    {"id":"logic","type":"expr","expr":"temp > 80"},
    {"id":"act.out","type":"http","url":"http://api/act"}
  ]
}`,
        },
        ts: Date.now(),
      },
    ]

    for (const c of chunks) {
      append(c)
      await sleep(350)
    }

    isBusy.value = false
  }

  // демо-початкові повідомлення
  async function mockBoot() {
    append({
      id: crypto.randomUUID(),
      role: 'agent',
      type: 'text',
      content: {text: 'Привіт 👋 Я агент цього flow. Постав запитання або надішли інструкцію.'},
      ts: Date.now(),
    })
    append({
      id: crypto.randomUUID(),
      role: 'agent',
      type: 'notice',
      content: {severity: 'info', text: 'Проєкт знайдено. Статус: healthy'},
      ts: Date.now(),
    })
  }

  return {isBusy, sendToAgent, mockBoot}
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}
