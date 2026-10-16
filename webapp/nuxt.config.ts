import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-08-06',
  ssr: false,
  devtools: { enabled: false },
  css: ['@fontsource-variable/atkinson-hyperlegible-next', 'maplibre-gl/dist/maplibre-gl.css', '~/assets/css/tema.css'],
  devServer: { host: '0.0.0.0', port: 3000 },
  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: { include: ['vue', 'maplibre-gl'] },
    server: { allowedHosts: ['.trycloudflare.com'] }, // tunnel per il telefono (HTTPS: GPS e fotocamera)
  },
  // stessa origine: il browser chiama /api/**, in produzione lo inoltra nginx, in dev (nuxt dev) Nitro.
  // BACKEND_URL: solo per nuxt dev in Docker (compose.dev.yaml), dove il backend e' http://backend:8000
  routeRules: { '/api/**': { proxy: `${process.env.BACKEND_URL ?? 'http://localhost:8000'}/**` } },
  app: {
    head: {
      htmlAttrs: { lang: 'it' },
      title: 'Sentinelle',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width,initial-scale=1,viewport-fit=cover' },
        { name: 'theme-color', content: '#eef1f5' },
        { name: 'description', content: 'Segnala incendi e fumo in Sardegna e ricevi gli avvisi per la tua casa e i tuoi terreni.' },
        { name: 'robots', content: 'noindex' },
        { name: 'mobile-web-app-capable', content: 'yes' },
      ],
      link: [
        { rel: 'manifest', href: '/manifest.webmanifest' },
        { rel: 'icon', type: 'image/svg+xml', href: '/icona.svg' },
      ],
    },
    pageTransition: { name: 'pagina', mode: 'out-in' },
  },
  runtimeConfig: { public: { apiBaseUrl: '/api' } },
})
