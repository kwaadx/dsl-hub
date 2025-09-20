import { Router } from 'express'
import { db } from '../db/client.js'
const r = Router()

r.get('/', (_req, res) => res.json({ up: true }))
r.get('/ready', async (_req, res) => {
  try { await db.$queryRaw`SELECT 1`; res.json({ ready: true }) }
  catch (e) { res.status(500).json({ ready: false, error: String(e) }) }
})
export default r
