import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { config } from './config.js';
import { healthRouter } from './routes/health.js';
import { apiRouter } from './routes/index.js';
import { sseBroadcast, sseHandler } from './sse.js';

const app = express();

app.use(cors({ origin: config.corsOrigin, credentials: true }));
app.use(express.json({ limit: '2mb' }));
app.use(morgan(config.nodeEnv === 'development' ? 'dev' : 'combined'));

app.use(healthRouter());
app.use(apiRouter());

app.get('/events', sseHandler);

app.post('/events/demo', (req, res) => {
  sseBroadcast('demo', { ts: Date.now(), payload: req.body ?? {} });
  res.json({ sent: true });
});

app.listen(config.port, config.host, () => {
  console.log(`[api] listening on http://${config.host}:${config.port} (mode=${config.mode}, env=${config.nodeEnv})`);
});
