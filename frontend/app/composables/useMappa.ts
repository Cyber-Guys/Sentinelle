import maplibregl, { type Map as MappaLibre } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import type { Tema } from './useTema'

// Protocollo pmtiles:// (storico incendi statico), registrato una sola volta
let pmtilesOk = false
export function registraPmtiles() {
  if (pmtilesOk) return
  maplibregl.addProtocol('pmtiles', new Protocol().tile)
  pmtilesOk = true
}

// Mappa base vettoriale CARTO, una per tema
export const stileMappa = (t: Tema) =>
  t === 'scuro'
    ? 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
    : 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

// Lo stile CARTO porta gia' l'attribuzione OSM + CARTO: la si mostra compatta (pulsante "i"),
// chiusa al primo caricamento per non coprire i controlli.
export function chiudiAttribuzione(m: MappaLibre) {
  m.once('load', () => m.getContainer().querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'))
}

// Colori dei layer coerenti con i token (MapLibre vuole valori, non variabili CSS)
export function coloriMappa(t: Tema) {
  const scuro = t === 'scuro'
  return {
    brace: scuro ? '#ff6a2b' : '#e8351f',
    ambra: scuro ? '#f5b83d' : '#d99a1e',
    macchia: scuro ? '#3fb37f' : '#2f8f63',
    cielo: scuro ? '#5aa9e6' : '#2f7fc0',
    viola: scuro ? '#b48cf2' : '#7c4dc4',
    bordo: scuro ? '#07090d' : '#ffffff',
    testo: scuro ? '#f3f1ec' : '#1a1a17',
    // incendi storici: da ambra tenue (vecchi) a brace (recenti)
    storico: ['interpolate', ['linear'], ['get', 'anno'], 2015, scuro ? '#c99a4a' : '#e2b45a', 2020, scuro ? '#ff8a3d' : '#ef7a2e', 2025, scuro ? '#ff4a1f' : '#d92d17'] as any,
    opacitaStorico: ['interpolate', ['linear'], ['get', 'anno'], 2015, scuro ? 0.12 : 0.18, 2025, scuro ? 0.32 : 0.38] as any,
  }
}
