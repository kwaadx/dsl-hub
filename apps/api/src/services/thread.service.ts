import { db } from '../db/client.js'
import { bus } from '../events/bus.js'
import type { MessagePayload } from '../types/message.js'
import { env } from '../config/env.js'
import { minutesAgo } from '../lib/time.js'

export async function handleUserMessage({ threadId, payload }: { threadId: string; payload: MessagePayload }) {
  const t = await db.thread.findUnique({ where: { id: threadId } })
  if (!t) throw { status: 404, message: 'thread not found' }

  if (t.status === 'NEW') await db.thread.update({ where: { id: threadId }, data: { status: 'IN_PROGRESS' } })

  const content = normalizePayload(payload)
  await db.message.create({ data: { threadId, role: 'user', format: content.format as any, content } })

  for (const token of ['Working',' ','on',' ','it','…']) {
    bus.emit('agent:token', { threadId, token })
    await new Promise(r => setTimeout(r, 120))
  }

  const reply: MessagePayload = { format: 'text', text: 'Draft pipeline generated (stub).' }
  const replyJson = normalizePayload(reply)
  await db.message.create({ data: { threadId, role: 'assistant', format: replyJson.format as any, content: replyJson } })

  bus.emit('agent:done', { threadId, success: true, summary: { note: 'stubbed' } })
  return { accepted: true }
}

export async function complete(threadId: string, status: string) {
  const upper = status.toUpperCase()
  const success = upper === 'SUCCESS'
  await db.thread.update({
    where: { id: threadId },
    data: {
      status: success ? 'SUCCESS' : 'FAILED',
      archived: success,
      archivedAt: success ? new Date() : null,
      closedAt: new Date()
    }
  })
  return true
}

export async function maybeRotate(threadId: string) {
  const t = await db.thread.findUnique({ where: { id: threadId } })
  if (!t) throw { status: 404, message: 'thread not found' }

  const shouldArchive =
      (t.archived || t.status === 'SUCCESS') &&
      andOlderThan(t.updatedAt, env.ARCHIVE_AFTER_MIN)

  if (!shouldArchive) return { rotated: false }

  if (!t.archived) {
    await db.thread.update({
      where: { id: threadId },
      data: {
        archived: true,
        archivedAt: new Date(),
        status: 'ARCHIVED',
        closedAt: new Date(),
      },
    })
  } else if (t.status !== 'ARCHIVED') {
    await db.thread.update({
      where: { id: threadId },
      data: { status: 'ARCHIVED' },
    })
  }

  const newThread = await db.thread.create({
    data: { flowId: t.flowId, status: 'NEW' },
  })

  return { rotated: true, newThread }
}

function andOlderThan(date: Date, min: number) {
  return date < minutesAgo(min)
}

function normalizePayload(p: MessagePayload): any {
  switch (p.format) {
    case 'text': return { format: 'text', text: p.text }
    case 'markdown': return { format: 'markdown', md: p.md }
    case 'json': return { format: 'json', json: p.json }
    case 'buttons': return { format: 'buttons', buttons: p.buttons, prompt: p.prompt }
    case 'card': return { format: 'card', card: p.card }
  }
}
