import { Router } from 'express';

export function apiRouter() {
  const r = Router();

  r.get('/api/hello', (_req, res) => {
    res.json({ message: 'Hello from dsl-hub-api' });
  });

  return r;
}
