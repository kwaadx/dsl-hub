import { fileURLToPath } from 'node:url'

import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { defineConfig, loadEnv } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default ({ mode }: { mode: string }) => {
  process.env = { ...process.env, ...loadEnv(mode, process.cwd()) }

  return defineConfig({
    server: {
      port: 3000,
      host: true,
      hmr: { clientPort: 443, protocol: 'wss', port: 3000 },
      allowedHosts: process.env.VITE_ALLOWED_HOST ? [process.env.VITE_ALLOWED_HOST] : [],
    },
    plugins: [
      vue(),
      Components({ dirs: [], resolvers: [PrimeVueResolver()] }),
      VitePWA({
        strategies: 'injectManifest',
        srcDir: '.',
        filename: 'service-worker.js',
        injectRegister: false,
        manifest: false,
        includeAssets: [
          'favicon/favicon.ico',
          'favicon/favicon-16x16.png',
          'favicon/favicon-32x32.png',
          'favicon/apple-touch-icon.png',
          'favicon/safari-pinned-tab.svg',
        ],
        devOptions: {
          enabled: true,
          type: 'module',
        },
        injectManifest: {
          globIgnores: ['manifest.json'],
        },
      }),
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
          manifest: './public/manifest.json',
        },
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'vuex', 'vuex-persist', 'vue-i18n'],
            primevue: ['primevue'],
            lodash: ['lodash'],
            three: ['three'],
            videoPlayer: ['@videojs-player/vue'],
            charts: ['chart.js'],
            showdown: ['showdown'],
          },
        },
      },
      chunkSizeWarningLimit: 700,
    },
    optimizeDeps: { include: [] },
  })
}
