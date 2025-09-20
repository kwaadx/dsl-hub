import { Router } from 'express'
import * as c from '../controllers/thread.controller.js'
const r = Router()

r.get('/:id/stream', c.stream)
r.post('/:id/message', c.message)
r.post('/:id/complete', c.complete)
r.post('/:id/maybe-rotate', c.maybeRotate)

export default r
