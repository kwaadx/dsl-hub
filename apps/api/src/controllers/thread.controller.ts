import type { Request, Response } from 'express'
import { sseHub } from '../lib/sse.js'
import { bus } from '../events/bus.js'
import * as s from '../services/thread.service.js'

export async function stream(req: Request, res: Response) {
  const threadId = String(req.params.id)
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')
  res.flushHeaders?.()

  sseHub.add(threadId, res)
  const hb = setInterval(() => res.write(': keep-alive\n\n'), 15000)

  const onToken = (p: { threadId: string; token: string }) => { if (p.threadId === threadId) sseHub.send(threadId, 'token', p) }
  const onDone  = (p: { threadId: string; summary?: any; success?: boolean }) => { if (p.threadId === threadId) sseHub.send(threadId, 'done', p) }
  bus.on('agent:token', onToken)
  bus.on('agent:done', onDone)

  req.on('close', () => { clearInterval(hb); bus.off('agent:token', onToken); bus.off('agent:done', onDone); sseHub.remove(threadId); res.end() })
}

export async function message(req: Request, res: Response) {
  const threadId = String(req.params.id)
  const body = req.body as any
  const payload = body?.payload ?? { format: 'text', text: String(body?.text ?? '') }
  const m = await s.handleUserMessage({ threadId, payload })
  res.status(202).json(m)
}

export async function complete(req: Request, res: Response) {
  const threadId = String(req.params.id)
  const ok = await s.complete(threadId, String(req.body?.status ?? 'SUCCESS'))
  res.json({ ok })
}

export async function maybeRotate(req: Request, res: Response) {
  const threadId = String(req.params.id)
  const result = await s.maybeRotate(threadId)
  res.json(result)
}
