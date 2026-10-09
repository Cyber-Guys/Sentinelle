import maplibregl, { type Map as MappaLibre, type StyleSpecification } from 'maplibre-gl'
import { layers, namedFlavor } from '@protomaps/basemaps'
import { Protocol } from 'pmtiles'
import type { Tema } from './useTema'

// Protocollo pmtiles:// (storico incendi statico), registrato una sola volta
let pmtilesOk = false
export function registraPmtiles() {
  if (pmtilesOk) return
  maplibregl.addProtocol('pmtiles', new Protocol().tile)
  pmtilesOk = true
}

// Mappa base Protomaps, tutta in locale: tile (public/tiles/sardegna.pmtiles), font e sprite (public/basemap/).
// Una per tema; flavor ritoccati sui token (fondo blu-notte, acqua, strade).
const FLAVOR = {
  scuro: {
    base: 'dark',
    ritocchi: {
      background: '#07090d', earth: '#11151c', water: '#0a1729', buildings: '#0d1117',
      minor_a: '#1d222c', minor_b: '#1d222c', minor_service: '#171b23', link: '#262c38', major: '#2a303d', highway: '#343b4a',
      park_a: '#101c17', park_b: '#101c17', wood_a: '#111b16', wood_b: '#111b16', scrub_a: '#121c17', scrub_b: '#121c17',
      boundaries: '#3a4357',
    },
  },
  chiaro: {
    base: 'light',
    ritocchi: { background: '#f6f4ef', earth: '#efece5', water: '#c4d9e8', major: '#ffffff', highway: '#ffffff' },
  },
} as const

export const stileMappa = (t: Tema): StyleSpecification => {
  const { base, ritocchi } = FLAVOR[t]
  const origine = typeof location !== 'undefined' ? location.origin : ''
  return {
    version: 8,
    glyphs: `${origine}/basemap/fonts/{fontstack}/{range}.pbf`,
    sprite: `${origine}/basemap/sprites/${base}`,
    sources: {
      protomaps: { type: 'vector', url: 'pmtiles:///tiles/sardegna.pmtiles', attribution: '\u00a9 <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>, <a href="https://protomaps.com">Protomaps</a>' },
    },
    layers: layers('protomaps', { ...namedFlavor(base), ...ritocchi }, { lang: 'it' }) as any,
  }
}

// Testi dei controlli MapLibre in italiano (letti dagli screen reader)
export const LOCALE_MAPPA = {
  'NavigationControl.ZoomIn': 'Ingrandisci',
  'NavigationControl.ZoomOut': 'Riduci',
  'NavigationControl.ResetBearing': 'Orienta a nord',
  'AttributionControl.ToggleAttribution': 'Mostra o nascondi le fonti della mappa',
  'Popup.Close': 'Chiudi',
}

// L'attribuzione (OSM + Protomaps) arriva dalla sorgente: la si mostra compatta (pulsante "i"),
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
