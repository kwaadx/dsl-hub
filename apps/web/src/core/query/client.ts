import {MutationCache, QueryCache, QueryClient} from '@tanstack/vue-query';
import {normalizeError} from '@/lib/normalizeError';
import {toastError} from '@/lib/toast';

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (query.meta?.silent) return;
      const e = normalizeError(error);
      toastError(e.status ? `${e.status}: ${e.message}` : e.message);
      // if (e.status === 401) { /* redirect / logout */ }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _vars, _ctx, mutation) => {
      if (mutation.meta?.silent) return;
      const e = normalizeError(error);
      toastError(e.status ? `${e.status}: ${e.message}` : e.message);
    },
  }),
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
    mutations: {
      retry: 0,
    },
  },
});
