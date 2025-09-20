import 'dotenv/config'
import { z } from 'zod'

const Env = z.object({
  NODE_ENV: z.enum(['development','test','production']).default('development'),
  PORT: z.coerce.number().default(8080),
  DATABASE_URL: z.string(),
  CORS_ORIGIN: z.string().default('*'),
  ARCHIVE_AFTER_MIN: z.coerce.number().default(30)
})

export const env = Env.parse(process.env)
