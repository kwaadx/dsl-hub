import { isHttpError } from '@/core/http/http';

export type NormalizedError = {
  message: string;
  status?: number;
  code?: string | number;
  details?: unknown;
};

export function normalizeError(err: unknown): NormalizedError {
  if (isHttpError(err)) {
    return {
      message: String(err.message).slice(0, 400),
      status: err.status,
      code: err.code,
      details: err.payload,
    };
  }
  if (err instanceof Error) {
    const anyErr = err as any;
    return {
      message: String(err.message).slice(0, 400),
      status: typeof anyErr?.status === 'number' ? anyErr.status : undefined,
      code: anyErr?.code,
      details: anyErr?.payload ?? anyErr?.data,
    };
  }
  return { message: 'Unknown error' };
}
