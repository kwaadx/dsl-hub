import { Router } from 'express'
import * as c from '../controllers/flow.controller.js'
const r = Router()

r.get('/', c.list)
r.post('/', c.create)
r.get('/:id', c.get)
r.delete('/:id', c.remove)
r.post('/:id/threads/new-or-active', c.newOrActiveThread)

export default r
