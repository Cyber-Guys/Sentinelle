import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-08-06',
  ssr: false,
  devtools: { enabled: false },
  modules: ['reka-ui/nuxt'],
  css: ['maplibre-gl/dist/maplibre-gl.css', '~/assets/css/tema.css'],
  devServer: { host: '::', port: 3000 },
  vite: { plugins: [tailwindcss()], optimizeDeps: { include: ['vue', 'maplibre-gl'] } },
  app: {
    head: {
      htmlAttrs: { lang: 'it' },
      title: 'Sentinelle',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width,initial-scale=1' },
        { name: 'theme-color', content: '#ea580c' },
      ],
      link: [{ rel: 'manifest', href: '/manifest.webmanifest' }],
    },
  },
  runtimeConfig: {
    public: { apiBaseUrl: 'http://localhost:8000' }, // NUXT_PUBLIC_API_BASE_URL
  },
})
