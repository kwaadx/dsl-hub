import { ref, watch } from 'vue'
import { useSSE } from '@/composables/net/useSSE'
import type { AgentEvent, ChatMessage, UserMessage } from '@/types/chat'

export type UseThreadAgentParams = {
  apiBase?: string
  flowId?: string
  threadId: string
  token?: string
  onAppend: (m: ChatMessage) => void
}

export function useThreadAgent(params: UseThreadAgentParams) {
  const { apiBase = (import.meta as any).env?.VITE_API_BASE_URL || '', threadId, token, onAppend } = params

  const isBusy = ref(false)

  function append(m: ChatMessage) {
    onAppend(m)
  }

  // --- SSE replay persistence ---
  const lastKey = `sse:last:${threadId}`
  const savedLast = (typeof window !== 'undefined' ? window.localStorage.getItem(lastKey) : null) || undefined

  const sse = useSSE(`${apiBase}/threads/${threadId}/events`, {
    token,
    headers: savedLast ? { 'Last-Event-ID': savedLast } : undefined,
    heartbeatMs: 25_000,
    retryBaseMs: 500,
    retryMaxMs: 10_000,
  })

  // --- De-duplication of SSE events ---
  const seenIds = new Set<string>()
  const seenOrder: string[] = []
  const SEEN_MAX = 1000
  function remember(id: string) {
    if (seenIds.has(id)) return
    seenIds.add(id)
    seenOrder.push(id)
    if (seenOrder.length > SEEN_MAX) {
      const old = seenOrder.shift()
      if (old) seenIds.delete(old)
    }
  }

  // --- Collapse run.stage notices ---
  const stageMsgId = ref<string | null>(null)

  // Start SSE immediately
  sse.start()

  watch([sse.lastEventName, sse.lastEvent, sse.lastId], ([name, dataStr, id]) => {
    if (!name) return

    // Deduplicate SSE events by id
    if (id) {
      try { localStorage.setItem(lastKey, id) } catch { /* ignore */ }
      if (seenIds.has(id)) return
      remember(id)
    }

    if (name === 'ping') return

    let data: any = dataStr
    // Primary parse path (server now guarantees JSON string, but be defensive)
    if (typeof dataStr === 'string') {
      try {
        data = dataStr ? JSON.parse(dataStr) : null
      } catch {
        // Fallback: attempt to coerce common non-JSON forms (single quotes)
        try {
          const maybe = dataStr.trim()
          if (maybe.startsWith('{') || maybe.startsWith('[')) {
            const coerced = maybe.replace(/'/g, '"')
            data = JSON.parse(coerced)
          }
        } catch {
          // leave as raw string
          data = dataStr
        }
      }
    }

    switch (name) {
      case 'run.started': {
        isBusy.value = true
        stageMsgId.value = null
        append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'info', text: 'Run started' }, ts: data?.ts || Date.now() })
        return
      }
      case 'run.stage': {
        const text = `Stage ${data?.stage ?? ''}: ${data?.status ?? ''}`.trim()
        const msgId = stageMsgId.value || crypto.randomUUID()
        stageMsgId.value = msgId
        append({ id: msgId, role: 'system', type: 'notice', content: { text }, ts: data?.ts || Date.now() })
        return
      }
      case 'message.created': {
        const m = data as any
        const id = m?.message_id || crypto.randomUUID()
        const role = m?.role === 'user' ? 'user' : 'agent'
        const ts = m?.ts || Date.now()
        if (m?.format === 'markdown' && m?.content?.text) {
          append({ id, role, type: 'text', content: { text: m.content.text }, ts })
        } else if (m?.format === 'json') {
          append({ id, role, type: 'code', content: { language: 'json', code: JSON.stringify(m.content ?? {}, null, 2) }, ts })
        } else if (m?.format === 'text' && typeof m?.content?.text === 'string') {
          append({ id, role, type: 'text', content: { text: m.content.text }, ts })
        }
        return
      }
      case 'agent.msg': {
        const m = data as any
        // Prefer message.created; ignore legacy agent.msg if it carries a message_id
        if (m?.message_id) return
        if (m?.format === 'markdown' && m?.content?.text) {
          append({ id: crypto.randomUUID(), role: 'agent', type: 'text', content: { text: m.content.text }, ts: m.ts || Date.now() })
        } else if (m?.format === 'json') {
          append({ id: crypto.randomUUID(), role: 'agent', type: 'code', content: { language: 'json', code: JSON.stringify(m.content ?? {}, null, 2) }, ts: m.ts || Date.now() })
        } else if (typeof m === 'string') {
          append({ id: crypto.randomUUID(), role: 'agent', type: 'text', content: { text: m }, ts: Date.now() })
        }
        return
      }
      case 'suggestion': {
        const s = data as any
        const text = s?.name ? `Знайдено готовий пайплайн: ${s.name}` : 'Знайдено готовий пайплайн'
        append({ id: crypto.randomUUID(), role: 'agent', type: 'text', content: { text }, ts: s?.ts || Date.now() })
        return
      }
      case 'issues': {
        const s = data as any
        append({ id: crypto.randomUUID(), role: 'agent', type: 'notice', content: { severity: 'warn', text: `Виявлено проблеми: ${s?.items?.length ?? 0}` }, ts: s?.ts || Date.now() })
        append({ id: crypto.randomUUID(), role: 'agent', type: 'code', content: { language: 'json', code: JSON.stringify(s ?? {}, null, 2) }, ts: s?.ts || Date.now() })
        return
      }
      case 'pipeline.created':
      case 'pipeline.published': {
        append({ id: crypto.randomUUID(), role: 'agent', type: 'code', content: { language: 'json', code: JSON.stringify(data ?? {}, null, 2) }, ts: data?.ts || Date.now() })
        return
      }
      case 'ui.ack': {
        const u = data as any
        const text = u?.msg || 'Подію прийнято'
        append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'success', text }, ts: u?.ts || Date.now() })
        return
      }
      case 'run.finished': {
        isBusy.value = false
        stageMsgId.value = null
        const sev = data?.status === 'succeeded' ? 'success' : data?.status === 'failed' ? 'error' : 'info'
        append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: sev, text: 'Run finished' }, ts: data?.ts || Date.now() })
        return
      }
    }
  })

  // Surface connection errors to UI
  watch(sse.error, (e) => {
    if (!e) return
    const msg = e?.message || String(e)
    append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'error', text: `SSE error: ${msg}` }, ts: Date.now() })
    if (msg.includes('204')) {
      try { localStorage.removeItem(lastKey) } catch { /* ignore */ }
    }
  })

  async function postMessage(text: string) {
    const url = `${apiBase}/threads/${threadId}/messages?run=1`
    const idem = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idem,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ role: 'user', format: 'text', content: { text } }),
      })
      if (!res.ok) {
        const txt = await res.text().catch(() => res.statusText)
        append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'error', text: `Send failed: ${res.status} ${txt?.slice?.(0, 160) || ''}` }, ts: Date.now() })
      }
    } catch (e: any) {
      const msg = e?.message || String(e)
      append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'error', text: `Network error: ${msg}` }, ts: Date.now() })
    }
  }

  async function postEvent(ev: any) {
    const url = `${apiBase}/threads/${threadId}/agent/event`
    const idem = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idem,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(ev),
      })
      if (!res.ok) {
        const txt = await res.text().catch(() => res.statusText)
        append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'error', text: `Event failed: ${res.status} ${txt?.slice?.(0, 160) || ''}` }, ts: Date.now() })
      }
    } catch (e: any) {
      const msg = e?.message || String(e)
      append({ id: crypto.randomUUID(), role: 'system', type: 'notice', content: { severity: 'error', text: `Network error: ${msg}` }, ts: Date.now() })
    }
  }

  async function sendToAgent(msg: UserMessage | AgentEvent) {
    // Build payload for backend
    if ((msg as any).role === 'user') {
      const um = msg as UserMessage
      isBusy.value = true
      return postMessage(um.content?.text ?? '')
    }

    // Route UI events to dedicated endpoint
    const ev = msg as AgentEvent
    return postEvent(ev)
  }

  // Optional boot message to keep ThreadChat.vue logic intact
  async function mockBoot() {
    append({
      id: crypto.randomUUID(),
      role: 'agent',
      type: 'notice',
      content: { severity: 'info', text: 'Підключення до агента…' },
      ts: Date.now(),
    })
  }

  return { isBusy, sendToAgent, mockBoot }
}
