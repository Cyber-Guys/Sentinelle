import maplibregl, { type Map as MappaLibre, type StyleSpecification } from 'maplibre-gl'
import { layers, namedFlavor } from '@protomaps/basemaps'
import { Protocol } from 'pmtiles'
import type { Tema } from './useTema'
import { h, render, type Component } from 'vue'
import type { Segnalazione } from './useApi'

// Protocollo pmtiles:// (storico incendi statico), registrato una sola volta
let pmtilesOk = false
export function registraPmtiles() {
  if (pmtilesOk) return
  maplibregl.addProtocol('pmtiles', new Protocol().tile)
  pmtilesOk = true
}

// Mappa base Protomaps, tutta in locale: tile (public/tiles/sardegna.pmtiles), font e sprite (public/basemap/).
// Si sovrascrivono solo i colori del flavor. Scuro "alla Waze notte": terra blu-ardesia, mare blu-notte
// piu' profondo e saturo, strade con gerarchia netta, verde e urbano appena accennati.
// Il fondo (`background`) e' uguale al mare: fuori dall'estratto si vede mare, non un vuoto.
const MARE_SCURO = '#0a1426'
const MARE_CHIARO = '#b4cfe6'
const FLAVOR = {
  scuro: {
    base: 'dark',
    costa: '#2b4568',
    ritocchi: {
      background: MARE_SCURO, water: MARE_SCURO, earth: '#1a2130',
      landcover: { grassland: '#1b2431', barren: '#1d2330', urban_area: '#1e2535', farmland: '#1b2330', glacier: '#1d2330', scrub: '#1a2530', forest: '#182632' },
      park_a: '#192733', park_b: '#192733', wood_a: '#182632', wood_b: '#182632', scrub_a: '#1a2530', scrub_b: '#1a2530',
      hospital: '#1e2535', industrial: '#1e2433', school: '#1e2535', pedestrian: '#1e2535', zoo: '#192733', military: '#1e2433',
      sand: '#232a36', beach: '#252c38', aerodrome: '#1e2535', runway: '#2c3445', glacier: '#1d2330', pier: '#2c3445',
      buildings: '#171d29',
      // strade: dalla piu' importante (chiara, spessa) alla minore (tenue)
      highway: '#8f9cb6', major: '#66728b', link: '#4f5a72', minor_a: '#323b4d', minor_b: '#2b3343', minor_service: '#262d3c', other: '#262d3c',
      highway_casing_early: '#121826', highway_casing_late: '#121826', major_casing_early: '#121826', major_casing_late: '#121826',
      link_casing: '#121826', minor_casing: '#141a27', minor_service_casing: '#141a27',
      bridges_highway: '#8f9cb6', bridges_major: '#66728b', bridges_link: '#4f5a72', bridges_minor: '#323b4d', bridges_other: '#262d3c',
      bridges_highway_casing: '#121826', bridges_major_casing: '#121826', bridges_link_casing: '#121826', bridges_minor_casing: '#141a27', bridges_other_casing: '#141a27',
      tunnel_highway: '#4a556c', tunnel_major: '#3a4459', tunnel_link: '#333c4f', tunnel_minor: '#262d3c', tunnel_other: '#232a38',
      railway: '#2e3647', boundaries: '#4a5670',
      // etichette nitide con alone scuro
      city_label: '#e4e8ef', city_label_halo: '#0c111c', subplace_label: '#98a2b5', subplace_label_halo: '#0c111c',
      roads_label_major: '#a9b2c3', roads_label_major_halo: '#121826', roads_label_minor: '#7c8698', roads_label_minor_halo: '#121826',
      ocean_label: '#5679a8', state_label: '#5e687c', state_label_halo: '#0c111c', country_label: '#8a93a6',
      address_label: '#6b7487', address_label_halo: '#121826',
    },
  },
  chiaro: {
    base: 'light',
    costa: '#8eb2d4',
    ritocchi: {
      background: MARE_CHIARO, water: MARE_CHIARO, earth: '#f1efe9', buildings: '#e4e1d9',
      landcover: { grassland: '#e9ece0', barren: '#ece9e1', urban_area: '#e8e5de', farmland: '#eeebe2', glacier: '#f4f4f2', scrub: '#e4e9dc', forest: '#dfe7d8' },
      park_a: '#e1e9d9', park_b: '#e1e9d9', wood_a: '#dfe7d8', wood_b: '#dfe7d8', scrub_a: '#e4e9dc', scrub_b: '#e4e9dc',
      highway_casing_early: '#d8d3c8', highway_casing_late: '#d8d3c8', major_casing_early: '#ddd8ce', major_casing_late: '#ddd8ce',
      major: '#ffffff', highway: '#ffffff', city_label: '#24231f', city_label_halo: '#f8f7f3',
    },
  },
} as const

export const stileMappa = (t: Tema): StyleSpecification => {
  const { base, ritocchi, costa } = FLAVOR[t]
  const origine = typeof location !== 'undefined' ? location.origin : ''
  const flavor = { ...namedFlavor(base), ...ritocchi } as any
  if ('landcover' in ritocchi) flavor.landcover = { ...namedFlavor(base).landcover, ...ritocchi.landcover }
  const livelli = layers('protomaps', flavor, { lang: 'it' }) as any[]
  // linea di costa: contorno sottile dei poligoni d'acqua, subito sopra il riempimento del mare
  const iAcqua = livelli.findIndex((l) => l.id === 'water') + 1
  livelli.splice(iAcqua, 0, {
    id: 'costa', type: 'line', source: 'protomaps', 'source-layer': 'water', filter: ['==', '$type', 'Polygon'],
    paint: { 'line-color': costa, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 12, 1.2] },
  })
  return {
    version: 8,
    glyphs: `${origine}/basemap/fonts/{fontstack}/{range}.pbf`,
    sprite: `${origine}/basemap/sprites/${base}`,
    sources: {
      protomaps: { type: 'vector', url: 'pmtiles:///tiles/sardegna.pmtiles', attribution: '\u00a9 <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>, <a href="https://protomaps.com">Protomaps</a>' },
    },
    layers: livelli,
  }
}

// Limiti della mappa: l'estratto copre lat 38.75-41.35 (bbox di genera_tiles). In latitudine si resta
// dentro l'estratto (a nord c'e' la Corsica, assente); in longitudine si concede piu' spazio perche' a
// est e a ovest c'e' solo mare aperto e il fondo dello stile e' gia' mare. Lo zoom minimo si ricalcola
// sulla finestra cosi' che i limiti riempiano sempre tutto il riquadro (nessuna banda, nemmeno a 2560 px).
const LIMITI: [[number, number], [number, number]] = [[5.6, 38.77], [12.3, 41.33]]
const yMerc = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))
export function limitaMappa(m: MappaLibre) {
  const [[o, s], [e, n]] = LIMITI
  const aggiorna = () => {
    const { clientWidth: w, clientHeight: h } = m.getContainer()
    if (!w || !h) return
    const fx = (e - o) / 360
    const fy = (yMerc(n) - yMerc(s)) / (2 * Math.PI)
    const zMin = Math.log2(Math.max(w / (512 * fx), h / (512 * fy))) + 0.02
    m.setMinZoom(Math.max(6, zMin))
  }
  m.setMaxBounds(LIMITI)
  aggiorna()
  m.on('resize', aggiorna)
}

// Testi di MapLibre in italiano, letti dagli screen reader (zoom e fonti sono nostri: ControlliMappa.vue)
export const LOCALE_MAPPA = {
  'Popup.Close': 'Chiudi',
}

// Popup della mappa con un componente Vue dentro (PopupIncendio, PopupMappa): niente pulsante
// di MapLibre (il nostro sta nell'intestazione) e niente focus all'apertura (anello solo da tastiera).
export function apriPopup(m: MappaLibre, lngLat: maplibregl.LngLatLike, comp: Component, props: Record<string, unknown>, corpo?: () => unknown) {
  const el = document.createElement('div')
  const popup = new maplibregl.Popup({ closeButton: false, focusAfterOpen: false, maxWidth: 'none', offset: 10, className: 'popup-sentinelle' })
  render(h(comp, { ...props, onChiudi: () => popup.remove() }, corpo ? { default: corpo } : undefined), el)
  popup.on('close', () => render(null, el))
  popup.setLngLat(lngLat).setDOMContent(el).addTo(m)
  // La mappa sta sotto header (in alto) e Segnala/navigazione (in basso): se il popup
  // ci finisce sotto, la mappa scorre quanto basta per liberarlo.
  requestAnimationFrame(() => {
    const r = popup.getElement()?.getBoundingClientRect()
    const c = m.getContainer().getBoundingClientRect()
    if (!r) return
    const sotto = r.bottom - (c.bottom - LIBERO.basso)
    const sopra = c.top + LIBERO.alto - r.top
    if (sotto > 0) m.panBy([0, sotto], { duration: 250 })
    else if (sopra > 0) m.panBy([0, -sopra], { duration: 250 })
  })
  return popup
}
// fasce occupate dai controlli flottanti, in px dai bordi della mappa
const LIBERO = { alto: 72, basso: 156 }

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
    grigio: scuro ? '#8a867e' : '#6d6960', // testo-3: falsi allarmi
    testo: scuro ? '#f3f1ec' : '#1a1a17',
    // incendi storici: da ambra tenue (vecchi) a brace (recenti)
    storico: ['interpolate', ['linear'], ['get', 'anno'], 2015, scuro ? '#c99a4a' : '#e2b45a', 2020, scuro ? '#ff8a3d' : '#ef7a2e', 2025, scuro ? '#ff4a1f' : '#d92d17'] as any,
    opacitaStorico: ['interpolate', ['linear'], ['get', 'anno'], 2015, scuro ? 0.12 : 0.18, 2025, scuro ? 0.32 : 0.38] as any,
  }
}

/*
  Pin pulsanti sui layer `circle`: un solo requestAnimationFrame per mappa anima gli aloni
  (non uno per pin), quindi il costo non cresce col numero di punti. Stesso disegno di `.pin`
  in tema.css. `onda`: si allarga e svanisce; `respiro`: cresce e cala piano (hotspot).
  `tratto`: anima il bordo invece del riempimento (anello della selezione).
  Con reduced-motion non parte: restano i valori statici dei layer (alone fisso).
*/
export type Alone = { layer: string; periodo: number; da: number; a: number; opacita: number; respiro?: boolean; tratto?: boolean }
export function animaAloni(m: MappaLibre, aloni: Alone[]) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return () => {}
  let raf = 0
  const passo = (t: number) => {
    for (const a of aloni) {
      if (!m.getLayer(a.layer)) continue
      const k = (t % a.periodo) / a.periodo
      const e = a.respiro ? (1 - Math.cos(k * 2 * Math.PI)) / 2 : 1 - (1 - k) ** 2
      m.setPaintProperty(a.layer, 'circle-radius', a.da + e * (a.a - a.da))
      m.setPaintProperty(a.layer, a.tratto ? 'circle-stroke-opacity' : 'circle-opacity', a.respiro ? a.opacita * (1 - 0.6 * e) : a.opacita * (1 - e))
    }
    raf = requestAnimationFrame(passo)
  }
  raf = requestAnimationFrame(passo)
  return () => cancelAnimationFrame(raf)
}

// Hotspot satellitari (app e cruscotto): punto brace piccolo + alone che respira, piu' lento delle segnalazioni.
export const ALONE_HOTSPOT: Alone = { layer: 'hotspot-alone', periodo: 3800, da: 7, a: 16, opacita: 0.4, respiro: true }
export function aggiungiHotspot(m: MappaLibre, c: ReturnType<typeof coloriMappa>, dati: any) {
  m.addSource('hotspot', { type: 'geojson', data: dati })
  m.addLayer({ id: 'hotspot-alone', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 12, 'circle-color': c.brace, 'circle-opacity': 0.22, 'circle-blur': 0.5 } })
  m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 5, 'circle-color': c.brace, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 1.5 } })
}

/*
  Segnalazioni con stato (storico nel cruscotto, proprie nell'app): `nuova` = punto `coloreNuova` con onda
  (layer `<id>-alone`, da animare con animaAloni), `confermata` = punto pieno `coloreConfermata` fermo con
  bordo chiaro, `archiviata` = anello grigio vuoto fermo. Proprieta' delle feature: id, stato, priorita, selezionata.
*/
export function geojsonSegnalazioni(l: Segnalazione[], selezionata: number | null = null) {
  return {
    type: 'FeatureCollection' as const,
    features: l.map((s) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [s.lon, s.lat] },
      properties: { id: s.id, stato: s.stato, priorita: s.priorita, selezionata: s.id === selezionata ? 1 : 0 },
    })),
  }
}
export function aggiungiPinSegnalazioni(m: MappaLibre, id: string, c: ReturnType<typeof coloriMappa>, dati: any, colori: { nuova: any; confermata: any }, prima?: string) {
  m.addSource(id, { type: 'geojson', data: dati })
  const stato = ['get', 'stato']
  const sel = ['==', ['get', 'selezionata'], 1]
  m.addLayer({ id: `${id}-alone`, type: 'circle', source: id, filter: ['==', stato, 'nuova'], paint: { 'circle-radius': 16, 'circle-color': colori.nuova, 'circle-opacity': 0.22, 'circle-blur': 0.3 } }, prima)
  m.addLayer({ id, type: 'circle', source: id, paint: {
    'circle-radius': ['case', sel, 10, ['==', stato, 'archiviata'], 6, 7] as any,
    'circle-color': ['match', stato, 'archiviata', 'rgba(0,0,0,0)', 'confermata', colori.confermata, colori.nuova] as any,
    'circle-stroke-color': ['match', stato, 'archiviata', c.grigio, 'confermata', c.testo, c.bordo] as any,
    'circle-stroke-width': ['case', sel, 3, ['==', stato, 'nuova'], 2, 2.5] as any,
  } }, prima)
}
export const aloneSegnalazioni = (id: string): Alone => ({ layer: `${id}-alone`, periodo: 2600, da: 9, a: 27, opacita: 0.45 })
