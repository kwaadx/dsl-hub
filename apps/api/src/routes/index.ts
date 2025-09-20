import { Router } from 'express'
import flows from './flow.routes.js'
import threads from './thread.routes.js'
import pipelines from './pipeline.routes.js'
import schemas from './schema.routes.js'
import summaries from './summary.routes.js'
import logs from './log.routes.js'

const r = Router()
r.use('/flows', flows)
r.use('/threads', threads)
r.use('/pipelines', pipelines)
r.use('/schemas', schemas)
r.use('/summaries', summaries)
r.use('/logs', logs)
export default r
