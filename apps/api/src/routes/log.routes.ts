import { Router } from 'express'
import * as c from '../controllers/log.controller.js'
const r = Router()

r.post('/', c.write)
export default r
