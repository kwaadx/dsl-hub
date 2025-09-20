import { Router } from 'express'
import * as c from '../controllers/summary.controller.js'
const r = Router()

r.get('/global', c.getGlobal)
r.post('/global', c.upsertGlobal)
r.get('/flow/:flowId/latest', c.flowLatest)
r.post('/flow/:flowId', c.flowCreate)
export default r
