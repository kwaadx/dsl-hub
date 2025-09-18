import 'dotenv/config';

export const config = {
  mode: process.env.MODE ?? 'prod',
  nodeEnv: process.env.NODE_ENV ?? 'production',
  logLevel: process.env.LOG_LEVEL ?? 'info',

  host: process.env.API_HOST ?? '0.0.0.0',
  port: Number(process.env.API_PORT ?? 3001),

  corsOrigin:
    process.env.CORS_ORIGIN ??
    (process.env.NODE_ENV === 'development' ? '*' : 'http://localhost:3000'),

  databaseUrl: process.env.DATABASE_URL,
};
