import { Router } from 'express'
import * as c from '../controllers/schema.controller.js'
const r = Router()

r.post('/', c.register)
r.get('/', c.list)
export default r
