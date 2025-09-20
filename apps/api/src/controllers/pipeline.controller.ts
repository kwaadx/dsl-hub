import type { Request, Response } from 'express'
import * as s from '../services/pipeline.service.js'

export async function latest(req: Request, res: Response) {
  const { flowId } = req.params as any
  res.json(await s.latest(flowId))
}
export async function create(req: Request, res: Response) {
  const { flowId } = req.params as any
  const { version = 'v0.1.0', schemaVersion = '3.0', content = {} } = req.body || {}
  res.status(201).json(await s.create({ flowId, version, schemaVersion, content }))
}
