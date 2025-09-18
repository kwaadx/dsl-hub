import type { Request, Response } from 'express';

type Client = { id: string; res: Response };

const clients = new Map<string, Client>();

export function sseHandler(req: Request, res: Response) {
  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
  });
  res.flushHeaders?.();

  res.write(`event: ping\ndata: "ready"\n\n`);

  clients.set(id, { id, res });

  req.on('close', () => {
    clients.delete(id);
  });
}

export function sseBroadcast(event: string, data: unknown) {
  const payload = typeof data === 'string' ? data : JSON.stringify(data, null, 0);
  for (const { res } of clients.values()) {
    res.write(`event: ${event}\n`);
    res.write(`data: ${payload}\n\n`);
  }
}
