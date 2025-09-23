import type { Response } from 'express'

export type Client = { id: string; res: Response }

export class SSEHub {
  private clients = new Map<string, Client>()
  add(id: string, res: Response) { this.clients.set(id, { id, res }) }
  remove(id: string) { this.clients.delete(id) }
  send(id: string, event: string, data: unknown) {
    const c = this.clients.get(id); if (!c) return
    c.res.write(`event: ${event}\n`)
    c.res.write(`data: ${JSON.stringify(data)}\n\n`)
  }
}
export const sseHub = new SSEHub()
