import type { Request, Response } from 'express'
import * as s from '../services/log.service.js'
export const write = async (req: Request, res: Response) => res.status(201).json(await s.write(req.body))
