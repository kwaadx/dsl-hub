export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestOptions<TBody = unknown> {
  method?: HttpMethod;
  path: string;
  body?: TBody;
  query?: Record<string, any>;
  headers?: Record<string, string>;
  signal?: AbortSignal | null;
  auth?: boolean;
}
