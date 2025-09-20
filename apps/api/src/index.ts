import { createServer } from 'http'
import app from './app.js'
import { env } from './config/env.js'
import { logger } from './config/logger.js'

const server = createServer(app)
server.listen(env.PORT, () => logger.info({ port: env.PORT }, 'listening'))

const shutdown = (sig: string) => () => {
  logger.info({ sig }, 'shutdown')
  server.close(() => process.exit(0))
}
;['SIGINT', 'SIGTERM'].forEach(s => process.on(s as any, shutdown(s)))
