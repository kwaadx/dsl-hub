import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import pinoHttp from 'pino-http'
import { env } from './config/env.js'
import { logger } from './config/logger.js'
import routes from './routes/index.js'
import healthRoutes from './health/routes.js'
import { errorHandler } from './middlewares/error.js'

const app = express()
app.use(helmet())
app.use(cors({ origin: env.CORS_ORIGIN.split(',') }))
app.use(express.json({ limit: '2mb' }))
app.use(pinoHttp({ logger }))

app.use('/health', healthRoutes)
app.use('/api', routes)

app.use(errorHandler)
export default app
