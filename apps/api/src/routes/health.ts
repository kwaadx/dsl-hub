import type { Request, Response, Router } from 'express';
import { Router as ExpressRouter } from 'express';

export function healthRouter(): Router {
  const r = ExpressRouter();

  r.get('/health', (_req: Request, res: Response) => {
    const uptime = process.uptime();
    res.status(200).json({
      status: 'ok',
      uptime,
      ts: new Date().toISOString(),
    });
  });

  return r;
}
