import { Router } from 'express'
import * as c from '../controllers/pipeline.controller.js'
const r = Router()

r.get('/flow/:flowId/latest', c.latest)
r.post('/flow/:flowId', c.create)

export default r
