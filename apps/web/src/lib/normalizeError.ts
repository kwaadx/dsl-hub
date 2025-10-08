import axios, { AxiosError } from 'axios';

export type NormalizedError = {
  message: string;
  status?: number;
  code?: string | number;
  details?: unknown;
};

export function normalizeError(err: unknown): NormalizedError {
  // Axios error shape
  if (axios.isAxiosError(err)) {
    const axErr = err as AxiosError<any>;
    const status = axErr.response?.status;
    const data = axErr.response?.data as any;
    const unified = data && typeof data === 'object' ? (data as any).error : null;
    const message =
      (unified && typeof unified.message === 'string' && unified.message) ||
      (data && (data.message || (typeof data.error === 'string' ? data.error : null) || data?.detail)) ||
      String(axErr.message);
    const code = (unified && unified.code) ?? (data && (data.code ?? data.errorCode)) ?? (axErr as any)?.code;
    return {
      message: String(message).slice(0, 400),
      status,
      code,
      details: data,
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
  return {message: 'Unknown error'};
}
