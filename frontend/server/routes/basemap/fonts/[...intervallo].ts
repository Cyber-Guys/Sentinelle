// In public/basemap/fonts ci sono solo gli intervalli latini. Per gli altri (arabo, tifinagh delle
// etichette nordafricane a zoom basso) senza questa rotta tornerebbe l'HTML della SPA e MapLibre
// riempirebbe la console di avvisi: rispondiamo con un pbf vuoto (messaggio protobuf valido, zero glifi).
export default defineEventHandler((event) => {
  setResponseHeader(event, 'content-type', 'application/x-protobuf')
  setResponseHeader(event, 'cache-control', 'public, max-age=86400')
  return new Uint8Array(0)
})
