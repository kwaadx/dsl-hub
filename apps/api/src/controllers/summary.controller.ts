import type { Request, Response } from 'express'
import * as s from '../services/summary.service.js'
export const getGlobal = async (_req: Request, res: Response) => res.json(await s.getGlobal())
export const upsertGlobal = async (req: Request, res: Response) => res.json(await s.upsertGlobal(req.body?.content ?? {}))
export const flowLatest = async (req: Request, res: Response) => res.json(await s.flowLatest(String(req.params.flowId)))
export const flowCreate = async (req: Request, res: Response) => res.status(201).json(await s.flowCreate(String(req.params.flowId), req.body?.content ?? {}))
