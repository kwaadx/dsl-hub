import type { Request, Response } from 'express'
import * as s from '../services/schema.service.js'
export const register = async (req: Request, res: Response) => res.status(201).json(await s.register(req.body))
export const list = async (_req: Request, res: Response) => res.json(await s.list())
