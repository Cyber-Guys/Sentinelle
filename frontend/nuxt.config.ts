import tailwindcss from '@tailwindcss/vite'
import { SCRIPT_TEMA } from './app/composables/useTema'

export default defineNuxtConfig({
  compatibilityDate: '2026-08-06',
  ssr: false,
  devtools: { enabled: false },
  modules: ['reka-ui/nuxt'],
  css: ['maplibre-gl/dist/maplibre-gl.css', '~/assets/css/tema.css'],
  devServer: { host: '::', port: 3000 },
  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: { include: ['vue', 'maplibre-gl'] },
    server: { allowedHosts: ['.trycloudflare.com'] }, // tunnel per il telefono (scripts/tunnel.sh)
  },
  // stessa origine: il browser chiama /api/**, Nitro inoltra al backend (niente CORS, funziona dal tunnel HTTPS)
  routeRules: { '/api/**': { proxy: 'http://localhost:8000/**' } },
  app: {
    head: {
      htmlAttrs: { lang: 'it' },
      title: 'Sentinelle',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width,initial-scale=1,viewport-fit=cover' },
        { name: 'theme-color', content: '#07090d' },
      ],
      link: [{ rel: 'manifest', href: '/manifest.webmanifest' }],
      // tema applicato prima del primo render: niente lampo chiaro/scuro
      script: [{ innerHTML: SCRIPT_TEMA, tagPosition: 'head' }],
      style: [{ innerHTML: "html{background:#07090d;color-scheme:dark}html[data-tema='chiaro']{background:#f6f4ef;color-scheme:light}" }],
    },
  },
  runtimeConfig: {
    public: { apiBaseUrl: '/api' }, // NUXT_PUBLIC_API_BASE_URL
  },
})
