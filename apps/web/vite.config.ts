import { fileURLToPath } from 'node:url'

import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, loadEnv } from 'vite'

export default ({ mode }: { mode: string }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const PORT = Number(env.WEB_PORT || 5173)
  const PUBLIC_HOST = env.PUBLIC_DEV_HOST || 'localhost'
  const USE_WSS = env.VITE_HMR_USE_WSS === 'true'

  return defineConfig({
    server: {
      host: true,
      port: PORT,
      hmr: USE_WSS
        ? { protocol: 'wss', host: PUBLIC_HOST, clientPort: 443 }
        : { protocol: 'ws', host: PUBLIC_HOST, port: PORT },
      allowedHosts: [PUBLIC_HOST],
      watch: { usePolling: !!env.WATCH_POLL, interval: 1000 } // корисно у Docker
    },
    plugins: [
      vue(),
      Components({ dirs: [], resolvers: [PrimeVueResolver()] }),
    ],
    resolve: {
      extensions: ['*', '.js', '.vue', '.json', '.ts'],
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    define: { __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: true },
    build: {
      rollupOptions: {
        input: {
          main: './index.html',
        },
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'vue-i18n'],
            primevue: ['primevue'],
            lodash: ['lodash'],
            pinia: ['pinia', 'pinia-plugin-persistedstate'],
          },
        },
      },
      chunkSizeWarningLimit: 700,
    },
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'vue-i18n',
        'pinia',
        'primevue',
        'lodash'
      ]
    },
  })
}
