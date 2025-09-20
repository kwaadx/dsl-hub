import type { Request, Response } from 'express'
import * as s from '../services/flow.service.js'

export async function list(_req: Request, res: Response) { res.json(await s.list()) }
export async function create(req: Request, res: Response) {
  const name = String((req.body as any)?.name ?? 'Flow ' + Date.now())
  res.status(201).json(await s.create({ name }))
}
export async function get(req: Request, res: Response) {
  const flow = await s.byId(String(req.params.id))
  if (!flow) return res.status(404).json({ error: 'not found' })
  res.json(flow)
}
export async function remove(req: Request, res: Response) {
  const ok = await s.remove(String(req.params.id))
  if (!ok) return res.status(404).json({ error: 'not found' })
  res.json({ ok: true })
}
export async function newOrActiveThread(req: Request, res: Response) {
  const flowId = String(req.params.id)
  const t = await s.newOrActiveThread(flowId)
  res.json(t)
}
