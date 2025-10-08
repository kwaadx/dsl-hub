import {ref, shallowRef, onBeforeUnmount} from 'vue'
import {fetchEventSource} from '@microsoft/fetch-event-source'

type UseSSEOptions = {
  token?: string
  headers?: Record<string, string>
  method?: 'GET' | 'POST'
  body?: BodyInit | null
  retryBaseMs?: number
  retryMaxMs?: number
  heartbeatMs?: number
}

export function useSSE(url: string, opts: UseSSEOptions = {}) {
  const isActive = ref(false)
  const lastEvent = shallowRef<string | null>(null)
  const lastEventName = ref<string | null>(null)
  const lastId = ref<string | null>(null)
  const error = shallowRef<Error | null>(null)

  const controller = new AbortController()
  let heartbeatTimer: number | null = null
  let reconnecting = false
  let retryDelay = opts.retryBaseMs ?? 500

  const headers: Record<string, string> = {Accept: 'text/event-stream', ...opts.headers}
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`

  function resetHeartbeat() {
    if (heartbeatTimer) clearTimeout(heartbeatTimer)
    if (opts.heartbeatMs) {
      heartbeatTimer = window.setTimeout(() => {
        stop()
        start()
      }, opts.heartbeatMs)
    }
  }

  async function start() {
    if (isActive.value) return
    isActive.value = true
    error.value = null

    reconnecting = false
    retryDelay = opts.retryBaseMs ?? 500

    const run = async () => {
      await fetchEventSource(url, {
        method: opts.method ?? 'GET',
        body: opts.body ?? undefined,
        headers,
        signal: controller.signal,
        async onopen(res) {
          if (res.ok && res.headers.get('content-type')?.includes('text/event-stream')) {
            resetHeartbeat()
            return
          }
          throw new Error(`Bad SSE response: ${res.status} ${res.statusText}`)
        },
        onmessage(ev) {
          lastEvent.value = ev.data ?? null
          lastEventName.value = ev.event ?? null
          lastId.value = ev.id ?? null
          resetHeartbeat()
        },
        onerror(err) {
          error.value = err
          as
          Error
          if (!reconnecting) reconnect()
        },
        onclose() {
          if (!reconnecting && isActive.value) reconnect()
        },
        openWhenHidden: true,
      })
    }

    const reconnect = async () => {
      reconnecting = true
      stop(false)
      await new Promise(r => setTimeout(r, retryDelay))
      retryDelay = Math.min(retryDelay * 2, opts.retryMaxMs ?? 10_000)
      reconnecting = false
      start()
    }

    run().catch((e) => {
      error.value = e
      as
      Error
      if (!reconnecting) {
        const _ = (async () => {
          await new Promise(r => setTimeout(r, retryDelay))
          retryDelay = Math.min(retryDelay * 2, opts.retryMaxMs ?? 10_000)
          start()
        })()
      }
    })
  }

  function stop(resetState = true) {
    if (!isActive.value) return
    controller.abort()
    if (heartbeatTimer) clearTimeout(heartbeatTimer)
    if (resetState) {
      isActive.value = false
    }
  }

  onBeforeUnmount(() => stop())

  return {
    isActive, lastEvent, lastEventName, lastId, error,
    start, stop,
  }
}
