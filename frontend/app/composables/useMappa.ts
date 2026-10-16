import maplibregl, { type Map as MappaLibre, type StyleSpecification } from 'maplibre-gl'
import { layers, namedFlavor } from '@protomaps/basemaps'
import { Protocol } from 'pmtiles'
import type { Tema } from './useTema'
import { h, render, type Component } from 'vue'
import type { Segnalazione } from './useApi'
import PopupIncendio from '~/components/PopupIncendio.vue'
import PopupHotspot from '~/components/PopupHotspot.vue'
import PopupMappa from '~/components/PopupMappa.vue'
import DettaglioInvaso from '~/components/DettaglioInvaso.vue'
import { Waves, Flame, TreePine } from '@lucide/vue'
import { TIPI, ORDINE_TIPI, coloriTipi, type Condivisa } from './useWaze'

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
  popup.on('close', () => { render(null, el); aperti.delete(popup) })
  aperti.add(popup)
  popup.setLngLat(lngLat).setDOMContent(el).addTo(m)
  // La mappa sta sotto header (in alto) e Segnala/navigazione (in basso): se il popup
  // ci finisce sotto, la mappa scorre quanto basta per liberarlo.
  requestAnimationFrame(() => {
    const r = popup.getElement()?.getBoundingClientRect()
    const c = m.getContainer().getBoundingClientRect()
    if (!r) return
    const f = fasce.get(m) ?? LIBERO
    const sotto = r.bottom - (c.bottom - f.basso)
    const sopra = c.top + f.alto - r.top
    const destra = r.right - (c.right - (f.destra ?? 0))
    const sinistra = c.left + (f.sinistra ?? 0) - r.left
    const dx = destra > 0 ? destra : sinistra > 0 ? -sinistra : 0
    const dy = sotto > 0 ? sotto : sopra > 0 ? -sopra : 0
    if (dx || dy) m.panBy([dx, dy], { duration: 250 })
  })
  return popup
}
// fasce occupate dai controlli flottanti, in px dai bordi della mappa
const LIBERO = { alto: 72, basso: 156 }
const aperti = new Set<maplibregl.Popup>()
// chiude i popup aperti con apriPopup (cruscotto su telefono: il foglio sale e li coprirebbe)
export function chiudiPopup() { [...aperti].forEach((p) => p.remove()) }
type Fasce = { alto: number; basso: number; destra?: number; sinistra?: number }
const fasce = new WeakMap<MappaLibre, Fasce>()
// fasce libere per mappa (cruscotto su telefono: il foglio in basso cambia altezza)
export function impostaFasceLibere(m: MappaLibre, f: Fasce) { fasce.set(m, f) }

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

/*
  Incendi attivi (app e cruscotto, da /incendi-attivi): hotspot FIRMS vicini raggruppati. Fino a zoom 11 un pin
  brace per incendio con alone che respira (raggio che cresce poco con le rilevazioni, badge col numero se >1);
  da zoom 11 l'area reale (pixel VIIRS 375 m uniti, brace semitrasparente con bordo) con i singoli punti dentro.
  Il layer cliccabile resta `hotspot` (pin) piu' `incendi-area` e `hotspot-punti`: vedi LIVELLI_HOTSPOT.
*/
export const ZOOM_AREA_INCENDI = 11
export const LIVELLI_HOTSPOT = ['hotspot', 'incendi-area', 'hotspot-punti']
export const TUTTI_LIVELLI_HOTSPOT = ['incendi-area', 'incendi-area-linea', 'hotspot-punti', 'hotspot-alone', 'hotspot', 'hotspot-badge']
export const ALONE_HOTSPOT: Alone = { layer: 'hotspot-alone', periodo: 3800, da: 8, a: 18, opacita: 0.4, respiro: true }
const geometrieIncendi = new Map<string, any>()
function sorgentiIncendi(dati: any) {
  const fs: any[] = dati?.features ?? []
  geometrieIncendi.clear()
  for (const f of fs) geometrieIncendi.set(f.properties.id, { area: f.geometry, centro: f.properties.centro })
  const props = (p: any) => ({ ...p, satelliti: (p.satelliti ?? []).join(', '), centro: undefined, punti: undefined })
  return {
    area: { type: 'FeatureCollection', features: fs.map((f) => ({ type: 'Feature', geometry: f.geometry, properties: props(f.properties) })) },
    pin: { type: 'FeatureCollection', features: fs.map((f) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: f.properties.centro }, properties: props(f.properties) })) },
    punti: { type: 'FeatureCollection', features: fs.flatMap((f) => (f.properties.punti ?? []).map((c: number[]) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: props(f.properties) }))) },
  }
}
export function aggiungiHotspot(m: MappaLibre, c: ReturnType<typeof coloriMappa>, dati: any) {
  const s = sorgentiIncendi(dati)
  m.addSource('incendi-area', { type: 'geojson', data: s.area as any })
  m.addSource('hotspot-punti', { type: 'geojson', data: s.punti as any })
  m.addSource('hotspot', { type: 'geojson', data: s.pin as any })
  const z = ZOOM_AREA_INCENDI
  m.addLayer({ id: 'incendi-area', type: 'fill', source: 'incendi-area', minzoom: z, paint: { 'fill-color': c.brace, 'fill-opacity': 0.28 } })
  m.addLayer({ id: 'incendi-area-linea', type: 'line', source: 'incendi-area', minzoom: z, paint: { 'line-color': c.brace, 'line-width': 1.6, 'line-opacity': 0.9 } })
  m.addLayer({ id: 'hotspot-punti', type: 'circle', source: 'hotspot-punti', minzoom: z, paint: { 'circle-radius': 3.5, 'circle-color': c.brace, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 1.2 } })
  m.addLayer({ id: 'hotspot-alone', type: 'circle', source: 'hotspot', maxzoom: z, paint: { 'circle-radius': 12, 'circle-color': c.brace, 'circle-opacity': 0.22, 'circle-blur': 0.5 } })
  m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', maxzoom: z, paint: {
    'circle-radius': ['interpolate', ['linear'], ['get', 'rilevazioni'], 1, 5, 10, 8.5] as any,
    'circle-color': c.brace, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 1.5 } })
  m.addLayer({ id: 'hotspot-badge', type: 'symbol', source: 'hotspot', maxzoom: z, filter: ['>', ['get', 'rilevazioni'], 1], layout: {
    'text-field': ['to-string', ['get', 'rilevazioni']], 'text-font': ['Noto Sans Medium'], 'text-size': 10,
    'text-offset': [0.95, -0.95], 'text-allow-overlap': true, 'text-ignore-placement': true } as any,
    paint: { 'text-color': c.testo, 'text-halo-color': c.bordo, 'text-halo-width': 1.6 } })
}
export function impostaHotspot(m: MappaLibre | null, dati: any) {
  if (!m?.getSource('hotspot')) return
  const s = sorgentiIncendi(dati)
  ;(m.getSource('incendi-area') as maplibregl.GeoJSONSource).setData(s.area as any)
  ;(m.getSource('hotspot-punti') as maplibregl.GeoJSONSource).setData(s.punti as any)
  ;(m.getSource('hotspot') as maplibregl.GeoJSONSource).setData(s.pin as any)
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

/*
  Incendi storici CFVA (app e cruscotto): perimetri da tile statici (public/tiles/storico.pmtiles), colore e
  opacita' per anno. Il filtro per anno e' istantaneo (setFilter: i dati sono gia' nei tile). Si aggiungono
  prima di ogni altro livello dati, cosi' pin e hotspot restano sopra.
*/
export const FILTRI_STORICO_INCENDI = [
  { id: '2025', etichetta: 'Stagione 2025', breve: '2025', dettaglio: "Solo l'ultima estate", da: 2025 },
  { id: '5', etichetta: 'Ultimi 5 anni', breve: '5 anni', dettaglio: '2021 \u2013 2025', da: 2021 },
  { id: 'tutti', etichetta: 'Dal 2015', breve: '2015+', dettaglio: 'Ultime 11 stagioni, 2015 \u2013 2025', da: 2015 },
] as const
const filtroAnni = (id: string) => ['>=', ['get', 'anno'], FILTRI_STORICO_INCENDI.find((f) => f.id === id)!.da] as any
const LIVELLI_STORICO_INCENDI = ['storico-riempimento', 'storico-linea']
export function aggiungiStoricoIncendi(m: MappaLibre, c: ReturnType<typeof coloriMappa>, filtro: string, visibile = true) {
  const layout = { visibility: visibile ? 'visible' : 'none' } as const
  const filter = filtroAnni(filtro)
  m.addSource('storico', { type: 'vector', url: 'pmtiles:///tiles/storico.pmtiles' })
  m.addLayer({ id: 'storico-riempimento', type: 'fill', source: 'storico', 'source-layer': 'incendi', layout, filter, paint: { 'fill-color': c.storico, 'fill-opacity': c.opacitaStorico } })
  m.addLayer({ id: 'storico-linea', type: 'line', source: 'storico', 'source-layer': 'incendi', layout, filter, paint: { 'line-color': c.storico, 'line-width': 0.7, 'line-opacity': 0.55 } })
}
export function impostaStoricoIncendi(m: MappaLibre | null, filtro: string, visibile = true) {
  for (const id of LIVELLI_STORICO_INCENDI) {
    if (!m?.getLayer(id)) continue
    m.setFilter(id, filtroAnni(filtro))
    m.setLayoutProperty(id, 'visibility', visibile ? 'visible' : 'none')
  }
}
// Tocco su un perimetro: popup dell'incendio, a meno che sotto il puntatore ci sia un pin (vince il pin).
// `pin`: id dei layer pin; `bloccato`: es. si sta scegliendo un punto sulla mappa.
export function clicIncendio(m: MappaLibre, pin: string[], bloccato: (pt: maplibregl.PointLike) => boolean = () => false) {
  m.on('click', 'storico-riempimento', (ev) => {
    const p = ev.features?.[0]?.properties
    if (!p || bloccato(ev.point)) return
    const layers = pin.filter((l) => m.getLayer(l))
    if (layers.length && m.queryRenderedFeatures(ev.point, { layers }).length) return
    apriPopup(m, ev.lngLat, PopupIncendio, { anno: Number(p.anno), data: p.data, comune: p.comune ? String(p.comune) : undefined, ettari: p.ettari != null ? Number(p.ettari) : null, bosco: p.bosco_ha != null ? Number(p.bosco_ha) : null })
  })
}

// Tocco su un incendio attivo (pin, area o punto): popup informativo; `pin` (segnalazioni) vince, l'incendio vince su storico e mappature.
// `simula` (cruscotto): il popup mostra "Simula scenario" e lo avvia dall'area dell'incendio.
export function clicHotspot(m: MappaLibre, pin: string[], bloccato: () => boolean = () => false, simula?: (lat: number, lon: number, titolo: string, area?: any) => void) {
  m.on('click', LIVELLI_HOTSPOT, (ev) => {
    const f = ev.features?.[0]
    if (!f || bloccato()) return
    const layers = pin.filter((l) => m.getLayer(l))
    if (layers.length && m.queryRenderedFeatures(ev.point, { layers }).length) return
    const p = f.properties ?? {}
    const n = (v: unknown) => (v == null || v === 'null' || v === '' ? null : Number(v))
    const str = (v: unknown) => (v == null || v === 'null' || v === '' ? null : String(v))
    const inc = geometrieIncendi.get(String(p.id))
    const area = inc?.area
    const [lon, lat] = inc?.centro ?? [ev.lngLat.lng, ev.lngLat.lat]
    apriPopup(m, [lon, lat], PopupHotspot, {
      lat, lon, rilevazioni: n(p.rilevazioni) ?? 1, ettari: n(p.ettari), prima: str(p.prima), ultima: str(p.ultima), confidenza: str(p.confidenza),
      comune: str(p.comune), frp_totale: n(p.frp_totale), frp_max: n(p.frp_max), satelliti: str(p.satelliti),
      onSimula: simula ? () => { chiudiPopup(); simula(lat, lon, str(p.comune) ?? '', area) } : undefined,
    })
  })
  m.on('mouseenter', LIVELLI_HOTSPOT, () => (m.getCanvas().style.cursor = 'pointer'))
  m.on('mouseleave', LIVELLI_HOTSPOT, () => (m.getCanvas().style.cursor = ''))
}

/*
  Segnaposto a icona (mappature dei cittadini): badge tondo di vetro scuro (chiaro nel tema chiaro),
  anello sottile e icona Lucide nel colore del tipo, punta minima sul punto, ombra appena accennata.
  Disegnati in modo sincrono su canvas (icona Lucide renderizzata in un div e ridisegnata con Path2D),
  cosi' l'immagine esiste prima del layer e `styleimagemissing` puo' rigenerarla al volo.
  Registrare con registraSegnaposti() a ogni style.load (setStyle cancella le immagini).
*/
export type Segnaposto = { id: string; icona: Component; colore: string; pieno?: boolean } // pieno: badge nel colore, icona scura
const LATO = 32, ALTO = 34, R = 12, CY = 15 // px logici: badge 24 + anello, punta di 4 px fino in fondo

// colori dei tipi un tono sotto i token (meno saturi), per pin e legenda delle mappature
export function toniMappature(t: Tema) {
  const scuro = t === 'scuro'
  return {
    cielo: scuro ? '#4f8fc2' : '#2a6a9e',
    ambra: scuro ? '#cf9a3a' : '#8a5c0b',
    viola: scuro ? '#9478c6' : '#6a46a6',
    grigio: scuro ? '#8a867e' : '#6d6960',
    vetro: scuro ? 'rgba(18,23,34,.92)' : 'rgba(255,255,255,.94)',
    anello: scuro ? 'rgba(255,255,255,.16)' : 'rgba(20,20,10,.16)',
    testo2: scuro ? '#a7a39a' : '#5b5850',
  }
}

function disegnaIcona(ctx: CanvasRenderingContext2D, icona: Component, riempi = false) {
  const el = document.createElement('div')
  render(h(icona as any), el)
  for (const n of Array.from(el.querySelectorAll('svg > *'))) {
    const a = (k: string) => Number(n.getAttribute(k) ?? 0)
    if (n.tagName === 'path') { const p = new Path2D(n.getAttribute('d') ?? ''); if (riempi) ctx.fill(p); ctx.stroke(p); continue }
    ctx.beginPath()
    if (n.tagName === 'circle') ctx.arc(a('cx'), a('cy'), a('r'), 0, Math.PI * 2)
    else if (n.tagName === 'line') { ctx.moveTo(a('x1'), a('y1')); ctx.lineTo(a('x2'), a('y2')) }
    else if (n.tagName === 'rect') ctx.roundRect(a('x'), a('y'), a('width'), a('height'), a('rx'))
    else if (n.tagName === 'polyline' || n.tagName === 'polygon') {
      const p = (n.getAttribute('points') ?? '').trim().split(/[\s,]+/).map(Number)
      for (let i = 0; i < p.length; i += 2) i ? ctx.lineTo(p[i]!, p[i + 1]!) : ctx.moveTo(p[i]!, p[i + 1]!)
      if (n.tagName === 'polygon') ctx.closePath()
    }
    ctx.stroke()
  }
  render(null, el)
}

function immagineSegnaposto(s: Segnaposto, tema: Tema, pr: number) {
  const cv = document.createElement('canvas')
  cv.width = LATO * pr; cv.height = ALTO * pr
  const ctx = cv.getContext('2d')!
  ctx.scale(pr, pr)
  const cx = LATO / 2, th = 0.32 // semi-apertura della punta (rad)
  const bx = cx + R * Math.cos(Math.PI / 2 + th), by = CY + R * Math.sin(Math.PI / 2 + th)
  ctx.beginPath()
  ctx.arc(cx, CY, R, Math.PI / 2 + th, Math.PI / 2 - th + Math.PI * 2)
  ctx.lineTo(cx, ALTO - 0.75)
  ctx.lineTo(bx, by)
  ctx.closePath()
  ctx.save()
  ctx.shadowColor = tema === 'scuro' ? 'rgba(0,0,0,.45)' : 'rgba(20,20,15,.16)'
  ctx.shadowBlur = 3; ctx.shadowOffsetY = 1
  ctx.fillStyle = s.pieno ? s.colore : toniMappature(tema).vetro
  ctx.fill()
  ctx.restore()
  ctx.lineWidth = 1.5; ctx.lineJoin = 'round'
  ctx.strokeStyle = s.pieno ? (tema === 'scuro' ? 'rgba(7,9,13,.55)' : 'rgba(255,255,255,.9)') : s.colore
  ctx.stroke()
  // icona 24x24 Lucide ridotta a 13 px, tratto nel colore del tipo
  ctx.save()
  ctx.translate(cx - 6.5, CY - 6.5); ctx.scale(13 / 24, 13 / 24)
  ctx.strokeStyle = s.pieno ? '#10141c' : s.colore; ctx.lineWidth = 2.3; ctx.lineCap = 'round'; ctx.lineJoin = 'round'
  disegnaIcona(ctx, s.icona)
  ctx.restore()
  return ctx.getImageData(0, 0, cv.width, cv.height)
}

export function registraSegnaposti(m: MappaLibre, segnaposti: Segnaposto[], tema: Tema) {
  const pr = Math.max(2, Math.ceil(window.devicePixelRatio || 1))
  for (const s of segnaposti) {
    if (m.hasImage(s.id)) m.removeImage(s.id)
    m.addImage(s.id, immagineSegnaposto(s, tema, pr), { pixelRatio: pr })
  }
}

// rete di sicurezza: un'immagine chiesta dal layer ma assente si rigenera subito (stesso tema corrente)
export function segnapostiMancanti(m: MappaLibre, segnaposti: () => Segnaposto[], tema: () => Tema) {
  m.on('styleimagemissing', (e: any) => {
    const s = segnaposti().find((x) => x.id === e.id)
    if (s && !m.hasImage(s.id)) registraSegnaposti(m, [s], tema())
  })
}

/*
  Rischio di oggi (GET /rischio/griglia): celle ~2 km (0,02 lat x 0,025 lon) colorate con la scala della
  priorita' (macchia -> ambra -> brace), semi-trasparenti, sotto storico e pin. Spento di default.
*/
export type GrigliaRischio = { celle: [number, number, number][]; aggiornato_il: string; meteo_simulato?: boolean }
export function geojsonRischio(g: GrigliaRischio | null) {
  const dx = 0.0125, dy = 0.01
  return {
    type: 'FeatureCollection' as const,
    features: (g?.celle ?? []).map(([lon, lat, v]) => ({
      type: 'Feature' as const,
      properties: { v },
      geometry: { type: 'Polygon' as const, coordinates: [[[lon - dx, lat - dy], [lon + dx, lat - dy], [lon + dx, lat + dy], [lon - dx, lat + dy], [lon - dx, lat - dy]]] },
    })),
  }
}
export const SOGLIE_RISCHIO = [0.45, 0.65] // sotto: basso, in mezzo: medio, sopra: alto (legenda)
export function aggiungiRischio(m: MappaLibre, c: ReturnType<typeof coloriMappa>, dati: any, visibile: boolean, prima?: string) {
  m.addSource('rischio', { type: 'geojson', data: dati })
  m.addLayer({ id: 'rischio', type: 'fill', source: 'rischio', layout: { visibility: visibile ? 'visible' : 'none' }, paint: {
    'fill-color': ['interpolate', ['linear'], ['get', 'v'], 0.3, c.macchia, 0.55, c.ambra, 0.8, c.brace] as any,
    // piu' trasparente da vicino: si legge la carta sotto
    'fill-opacity': ['interpolate', ['linear'], ['zoom'], 7, 0.42, 11, 0.22] as any,
    'fill-antialias': false,
  } }, prima && m.getLayer(prima) ? prima : undefined)
}
export function impostaRischio(m: MappaLibre | null, dati: any, visibile: boolean) {
  if (!m?.getLayer('rischio')) return
  ;(m.getSource('rischio') as maplibregl.GeoJSONSource).setData(dati)
  m.setLayoutProperty('rischio', 'visibility', visibile ? 'visible' : 'none')
}

/*
  Scenario di propagazione (POST /simulazione): un'area per ora (cumulativa), filtrate per `ora <= cursore`.
  Le ore vecchie sono ambra tenue, la corrente brace; si disegnano le piu' recenti sotto (sort-key) cosi'
  ogni ora resta un anello leggibile. Fronte corrente = linea brace con bagliore; origine = pin brace pulsante.
*/
export type Simulazione = {
  origine: { lat: number; lon: number; comune?: string | null }; inizio: string; ore: number; risoluzione_m: number
  fotogrammi: { ora: number; area: any; ettari: number; fronte_km: number; vento: { kmh: number; da_gradi: number }; umidita: number }[]
  comuni: { nome: string; raggiunto_ora: number }[]
  acqua: { nome: string; tipo: 'punto_acqua' | 'invaso' | string; distanza_km: number; lat: number; lon: number; riempimento?: number; volume_mm3?: number }[]
  note: string; durata_s?: number
}
const LAYER_SCENARIO = ['scenario-aree', 'scenario-bagliore', 'scenario-fronte', 'scenario-origine-alone', 'scenario-origine']
export const ALONE_SCENARIO: Alone = { layer: 'scenario-origine-alone', periodo: 2000, da: 9, a: 30, opacita: 0.55 }
export function aggiungiScenario(m: MappaLibre, c: ReturnType<typeof coloriMappa>, s: Simulazione, ora: number) {
  if (m.getSource('scenario')) rimuoviScenario(m)
  m.addSource('scenario', { type: 'geojson', data: { type: 'FeatureCollection', features: s.fotogrammi.map((f) => ({ type: 'Feature', properties: { ora: f.ora }, geometry: f.area })) } as any })
  m.addSource('scenario-origine', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [s.origine.lon, s.origine.lat] } } as any })
  m.addLayer({ id: 'scenario-aree', type: 'fill', source: 'scenario', layout: { 'fill-sort-key': ['-', 0, ['get', 'ora']] as any }, paint: { 'fill-antialias': false } })
  m.addLayer({ id: 'scenario-bagliore', type: 'line', source: 'scenario', paint: { 'line-color': c.brace, 'line-width': 9, 'line-blur': 6, 'line-opacity': 0.45 } })
  m.addLayer({ id: 'scenario-fronte', type: 'line', source: 'scenario', layout: { 'line-join': 'round' }, paint: { 'line-color': c.brace, 'line-width': 2.4 } })
  m.addLayer({ id: 'scenario-origine-alone', type: 'circle', source: 'scenario-origine', paint: { 'circle-radius': 18, 'circle-color': c.brace, 'circle-opacity': 0.3, 'circle-blur': 0.3 } })
  m.addLayer({ id: 'scenario-origine', type: 'circle', source: 'scenario-origine', paint: { 'circle-radius': 7, 'circle-color': c.brace, 'circle-stroke-color': c.testo, 'circle-stroke-width': 2.5 } })
  impostaOraScenario(m, c, ora)
}
export function impostaOraScenario(m: MappaLibre | null, c: ReturnType<typeof coloriMappa>, ora: number) {
  if (!m?.getLayer('scenario-aree')) return
  const o = ['get', 'ora']
  m.setFilter('scenario-aree', ['<=', o, ora])
  m.setFilter('scenario-bagliore', ['==', o, ora])
  m.setFilter('scenario-fronte', ['==', o, ora])
  // gradiente relativo al cursore: ore vecchie ambra tenue, ora corrente brace piena
  const eta: any = ['-', ora, o]
  m.setPaintProperty('scenario-aree', 'fill-color', ['interpolate', ['linear'], eta, 0, c.brace, 3, c.ambra] as any)
  // le aree sono cumulative e si sovrappongono: l'opacita' delle ore passate si divide tra loro, cosi' il nucleo
  // (bruciato da piu' tempo) resta il piu' denso ma non supera ~55% anche a +24 h
  const vecchie = Math.min(0.2, 1 - Math.pow(1 - 0.5, 1 / Math.max(1, ora - 1)))
  m.setPaintProperty('scenario-aree', 'fill-opacity', ['case', ['==', eta, 0], 0.34, vecchie] as any)
}
export function rimuoviScenario(m: MappaLibre | null) {
  if (!m) return
  for (const l of LAYER_SCENARIO) if (m.getLayer(l)) m.removeLayer(l)
  for (const s of ['scenario', 'scenario-origine']) if (m.getSource(s)) m.removeSource(s)
}
export function limitiScenario(s: Simulazione): [[number, number], [number, number]] | null {
  const g = s.fotogrammi.at(-1)?.area
  let o = Infinity, so = Infinity, e = -Infinity, n = -Infinity
  const visita = (x: any) => { if (typeof x[0] === 'number') { o = Math.min(o, x[0]); e = Math.max(e, x[0]); so = Math.min(so, x[1]); n = Math.max(n, x[1]) } else x.forEach(visita) }
  if (g?.coordinates) visita(g.coordinates)
  return isFinite(o) ? [[o, so], [e, n]] : null
}

/*
  Risorse idriche (GET /invasi): i ~33 invasi del sistema regionale, dove elicotteri e Canadair attingono.
  Segnaposto a icona Waves in cielo (come le mappature) con la percentuale di riempimento sotto, da zoom 8.
*/
export const SEGNAPOSTO_INVASO = (t: Tema): Segnaposto => ({ id: 'invaso', icona: Waves, colore: toniMappature(t).cielo })
export function aggiungiInvasi(m: MappaLibre, t: Tema, dati: any, visibile: boolean) {
  if (m.getSource('invasi')) return
  const tm = toniMappature(t)
  registraSegnaposti(m, [SEGNAPOSTO_INVASO(t)], t)
  m.addSource('invasi', { type: 'geojson', data: dati })
  m.addLayer({ id: 'invasi', type: 'symbol', source: 'invasi', layout: {
    visibility: visibile ? 'visible' : 'none',
    'icon-image': 'invaso', 'icon-anchor': 'bottom', 'icon-allow-overlap': true, 'icon-ignore-placement': true,
    'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.75, 11, 1] as any,
    'text-field': ['step', ['zoom'], '', 8, ['concat', ['to-string', ['get', 'riempimento']], '%']] as any,
    'text-font': ['Noto Sans Medium'], 'text-size': 11, 'text-anchor': 'top', 'text-offset': [0, 0.15], 'text-optional': true,
  }, paint: { 'text-color': tm.cielo, 'text-halo-color': tm.vetro, 'text-halo-width': 1.5 } })
}
export function impostaInvasi(m: MappaLibre | null, dati: any, visibile: boolean) {
  if (!m?.getLayer('invasi')) return
  ;(m.getSource('invasi') as maplibregl.GeoJSONSource).setData(dati)
  m.setLayoutProperty('invasi', 'visibility', visibile ? 'visible' : 'none')
}
export function clicInvasi(m: MappaLibre, bloccato: () => boolean = () => false) {
  m.on('click', 'invasi', (ev) => {
    const f = ev.features?.[0]
    if (!f || bloccato()) return
    const p = f.properties ?? {}
    apriPopup(m, (f.geometry as any).coordinates, PopupMappa, {
      icona: Waves, tinta: [toniMappature('scuro').cielo, toniMappature('chiaro').cielo],
      etichetta: 'Risorsa idrica · invaso', titolo: p.nome, sottotitolo: 'Attingimento per elicotteri e Canadair',
    }, () => h(DettaglioInvaso, { riempimento: Number(p.riempimento), volume: Number(p.volume_mm3), capacita: Number(p.capacita_mm3), data: String(p.data_dato), fonte: String(p.fonte) }))
  })
  m.on('mouseenter', 'invasi', () => (m.getCanvas().style.cursor = 'pointer'))
  m.on('mouseleave', 'invasi', () => (m.getCanvas().style.cursor = ''))
}

/*
  Mappa condivisa (Waze per gli incendi): segnaposto a icona per tipo. Tre varianti per tipo:
  `tenue` (Da verificare: vetro con anello, semitrasparente, niente alone), `pieno` (Probabile, Comunita',
  Operatori: badge nel colore del tipo con alone pulsante) e `spento` (Probabilmente spento / Spento: grigio).
  Le proprie hanno un anello in piu' (layer `condivise-mia`). Aloni e anello sono centrati sul badge (19 px sopra il punto).
*/
export function segnapostiCondivise(t: Tema): Segnaposto[] {
  const c = coloriTipi(t), g = toniMappature(t).grigio
  return ORDINE_TIPI.flatMap((k) => [
    { id: `seg-${k}`, icona: TIPI[k].icona, colore: c[k] },
    { id: `seg-${k}-pieno`, icona: TIPI[k].icona, colore: c[k], pieno: true },
    { id: `seg-${k}-spento`, icona: TIPI[k].icona, colore: g },
  ])
}
export function variante(s: Condivisa) {
  if (s.probabilmente_spento || s.stato_ufficiale === 'spento') return 'spento'
  return s.affidabilita.livello === 'da_verificare' ? 'tenue' : 'pieno'
}
export function geojsonCondivise(l: Condivisa[], selezionata: number | null = null) {
  return {
    type: 'FeatureCollection' as const,
    features: l.map((s) => {
      const v = variante(s)
      return {
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [s.lon, s.lat] },
        properties: { id: s.id, tipo: s.tipo, variante: v, img: v === 'tenue' ? `seg-${s.tipo}` : `seg-${s.tipo}-${v}`, mia: s.mia ? 1 : 0, sel: s.id === selezionata ? 1 : 0 },
      }
    }),
  }
}
const SU_BADGE: [number, number] = [0, -19]
export function aggiungiCondivise(m: MappaLibre, t: Tema, dati: any) {
  registraSegnaposti(m, segnapostiCondivise(t), t)
  const c = coloriTipi(t)
  m.addSource('condivise', { type: 'geojson', data: dati })
  const colore = ['match', ['get', 'tipo'], ...ORDINE_TIPI.flatMap((k) => [k, c[k]]), c.fuoco] as any
  m.addLayer({ id: 'condivise-alone', type: 'circle', source: 'condivise', filter: ['==', ['get', 'variante'], 'pieno'],
    paint: { 'circle-radius': 18, 'circle-color': colore, 'circle-opacity': 0.25, 'circle-blur': 0.3, 'circle-translate': SU_BADGE } })
  m.addLayer({ id: 'condivise-mia', type: 'circle', source: 'condivise', filter: ['any', ['==', ['get', 'mia'], 1], ['==', ['get', 'sel'], 1]],
    paint: { 'circle-radius': ['case', ['==', ['get', 'sel'], 1], 18, 16] as any, 'circle-color': 'rgba(0,0,0,0)', 'circle-translate': SU_BADGE,
      'circle-stroke-width': ['case', ['==', ['get', 'sel'], 1], 2.5, 1.5] as any, 'circle-stroke-color': t === 'scuro' ? '#f3f1ec' : '#1a1a17',
      'circle-stroke-opacity': ['case', ['==', ['get', 'sel'], 1], 1, 0.75] as any } })
  m.addLayer({ id: 'condivise', type: 'symbol', source: 'condivise', layout: {
    'icon-image': ['get', 'img'] as any, 'icon-anchor': 'bottom', 'icon-allow-overlap': true, 'icon-ignore-placement': true,
    'symbol-sort-key': ['match', ['get', 'variante'], 'pieno', 2, 'tenue', 1, 0] as any,
  }, paint: { 'icon-opacity': ['match', ['get', 'variante'], 'tenue', 0.7, 'spento', 0.8, 1] as any } })
}
export const ALONE_CONDIVISE: Alone = { layer: 'condivise-alone', periodo: 2600, da: 12, a: 28, opacita: 0.45 }

/*
  Operativo (solo cruscotto): basi reali (GET /basi, dati/basi.json da fonti aperte) e flotta SIMULATA (GET /flotta).
  Forme proprie, mai tonde (i cerchi sono di segnalazioni e mappature):
  - mezzi = sagome viste dall'alto (autobotte, elicottero col rotore, Canadair) a gradiente vivo per stato, bordo
    bianco semitrasparente, glow colorato in intervento, ruotate sulla rotta. Aerei: ombra spostata e sfocata (quota).
  - basi = badge squircle con punta (pin stile iOS), gradiente vivo, glifo bianco Lucide (Flame, TreePine) o H,
    bordo interno chiaro, glow colorato e ombra a terra.
  Tutto disegnato su canvas (pixelRatio >= 2) e ri-registrato a ogni style.load col tema corrente.
*/
type Ente = 'VVF' | 'CFVA' | 'AIB'
// palette viva stile iOS, uguale nei due temi: [alto, basso] del gradiente
export const ENTI_BASI = {
  VVF: { etichetta: 'Vigili del Fuoco', grad: ['#FF6A3D', '#FF2D55'], colore: (_t: Tema) => '#FF2D55' },
  CFVA: { etichetta: 'Corpo Forestale (CFVA)', grad: ['#34E089', '#0FB872'], colore: (_t: Tema) => '#0FB872' },
  AIB: { etichetta: 'Basi aeree AIB', grad: ['#7C6CFF', '#5E3BEE'], colore: (_t: Tema) => '#5E3BEE' },
} as const

// stato del mezzo -> colore vivo (legenda nel pannello Livelli)
export const STATI_MEZZO = [
  { id: 'mov', etichetta: 'In movimento / in volo', stati: ['In movimento', 'In volo'], colore: (_t: Tema) => '#3BA7FF' },
  { id: 'posto', etichetta: 'Sul posto / lancio', stati: ['Sul posto', 'Lancio'], colore: (_t: Tema) => '#FF6A3D' },
  { id: 'acqua', etichetta: 'Carico acqua', stati: ['Carico acqua'], colore: (_t: Tema) => '#2DD4F0' },
  { id: 'pattuglia', etichetta: 'Pattuglia / ricognizione', stati: ['Pattuglia', 'Ricognizione'], colore: (_t: Tema) => '#34E089' },
  { id: 'base', etichetta: 'In base', stati: ['In base'], colore: (t: Tema) => (t === 'scuro' ? '#C9D1DC' : '#9AA5B4') },
] as const
export const statoMezzo = (s: string) => STATI_MEZZO.find((x) => (x.stati as readonly string[]).includes(s)) ?? STATI_MEZZO[4]
export type Famiglia = 'terra' | 'eli' | 'can'
export const FAMIGLIE: Record<Famiglia, string> = { terra: 'Mezzo di terra', eli: 'Elicottero', can: 'Canadair' }
export const famigliaMezzo = (m: { categoria: string; tipo: string }): Famiglia => (m.categoria === 'terra' ? 'terra' : m.tipo.startsWith('Canadair') ? 'can' : 'eli')

const L_MEZZO = 44 // lato del canvas dei mezzi, in px css; centro = posizione del mezzo, muso verso nord (margine per il glow)
const DETTAGLIO = 'rgba(10,13,19,.55)' // vetri e motori sopra il colore pieno

// #rrggbb verso il bianco; altri formati invariati
function schiarisci(col: string, k: number) {
  const m = /^#([0-9a-f]{6})$/i.exec(col); if (!m) return col
  const n = parseInt(m[1]!, 16), x = (v: number) => Math.round(v + (255 - v) * k)
  return `rgb(${x(n >> 16)},${x((n >> 8) & 255)},${x(n & 255)})`
}
const alfa = (col: string, a: number) => col + Math.round(a * 255).toString(16).padStart(2, '0')
function tela(w: number, h: number, pr: number) {
  const cv = document.createElement('canvas')
  cv.width = w * pr; cv.height = h * pr
  const ctx = cv.getContext('2d')!
  ctx.scale(pr, pr); ctx.lineJoin = 'round'; ctx.lineCap = 'round'
  return { cv, ctx }
}
function rr(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r) }

// sagoma piena, senza dettagli: serve anche per l'ombra
function sagoma(ctx: CanvasRenderingContext2D, f: Famiglia) {
  const c = L_MEZZO / 2
  ctx.beginPath()
  if (f === 'terra') { // autobotte: cabina + cisterna, 12 x 26
    ctx.roundRect(c - 6, c - 13, 12, 26, [4.5, 4.5, 2.5, 2.5])
  } else if (f === 'eli') { // fusoliera a goccia + trave di coda + piano di coda
    ctx.ellipse(c, c - 3, 5.2, 8.5, 0, 0, Math.PI * 2)
    ctx.roundRect(c - 1.5, c + 3, 3, 14, 1.5)
    ctx.roundRect(c - 4.8, c + 14, 9.6, 2.8, 1.4)
  } else { // Canadair: fusoliera lunga, ala alta dritta, piano di coda
    ctx.roundRect(c - 2.8, c - 16, 5.6, 31, [2.8, 2.8, 1.6, 1.6])
    ctx.roundRect(c - 17, c - 5, 34, 5.2, 2.4)
    ctx.roundRect(c - 7, c + 11, 14, 3.6, 1.6)
  }
}
function dettagli(ctx: CanvasRenderingContext2D, f: Famiglia) {
  const c = L_MEZZO / 2
  ctx.fillStyle = DETTAGLIO
  if (f === 'terra') {
    rr(ctx, c - 4.4, c - 10.5, 8.8, 3, 1.3); ctx.fill() // parabrezza
    ctx.fillStyle = 'rgba(255,255,255,.35)'; rr(ctx, c - 3.4, c - 4, 6.8, 14, 2.6); ctx.fill() // cisterna lucida
  } else if (f === 'eli') {
    ctx.beginPath(); ctx.ellipse(c, c - 7, 3, 3, 0, Math.PI, Math.PI * 2); ctx.fill() // cupola
  } else {
    rr(ctx, c - 1.8, c - 14.5, 3.6, 3, 1.2); ctx.fill() // cabina
    for (const x of [-8.5, 8.5]) { rr(ctx, c + x - 1.6, c - 8, 3.2, 6, 1.4); ctx.fill() } // motori
  }
}
function immagineMezzo(f: Famiglia, colore: string, t: Tema, pr: number, glow = false) {
  const { ctx } = tela(L_MEZZO, L_MEZZO, pr)
  const c = L_MEZZO / 2
  if (f === 'eli') { // disco del rotore: vetro colorato con anello
    ctx.beginPath(); ctx.arc(c, c - 3, 16, 0, Math.PI * 2)
    ctx.fillStyle = alfa(colore, 0.14); ctx.fill()
    ctx.strokeStyle = alfa(colore, 0.75); ctx.lineWidth = 1; ctx.stroke()
  }
  sagoma(ctx, f)
  ctx.save(); ctx.shadowColor = alfa(colore, glow ? 0.95 : t === 'scuro' ? 0.5 : 0.3); ctx.shadowBlur = glow ? 10 : 4
  ctx.fillStyle = colore; ctx.fill(); if (glow) ctx.fill(); ctx.restore()
  const g = ctx.createLinearGradient(0, c - 16, 0, c + 16)
  g.addColorStop(0, schiarisci(colore, 0.4)); g.addColorStop(1, colore)
  ctx.fillStyle = g; ctx.fill()
  ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.lineWidth = 1; ctx.stroke()
  dettagli(ctx, f)
  return ctx.getImageData(0, 0, L_MEZZO * pr, L_MEZZO * pr)
}
function immagineOmbra(f: Famiglia, t: Tema, pr: number) {
  const { ctx } = tela(L_MEZZO, L_MEZZO, pr)
  ctx.filter = f === 'terra' ? 'blur(1px)' : 'blur(2.6px)'
  sagoma(ctx, f)
  ctx.fillStyle = t === 'scuro' ? 'rgba(0,0,0,.5)' : 'rgba(20,25,40,.18)'; ctx.fill()
  return ctx.getImageData(0, 0, L_MEZZO * pr, L_MEZZO * pr)
}

// basi: badge squircle (superellisse n=4) con punta in basso, 40 x 46, ancorato alla punta
const W_BASE = 40, H_BASE = 46, LATO_B = 26, Y0 = 5, PUNTA = 37
function squircle(ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
  const n = 4.5, N = 72
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI * 2, co = Math.cos(a), si = Math.sin(a)
    const x = cx + r * Math.sign(co) * Math.abs(co) ** (2 / n), y = cy + r * Math.sign(si) * Math.abs(si) ** (2 / n)
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
  }
  ctx.closePath()
}
function formaBase(ctx: CanvasRenderingContext2D) {
  const c = W_BASE / 2, cy = Y0 + LATO_B / 2
  ctx.beginPath(); squircle(ctx, c, cy, LATO_B / 2)
  ctx.moveTo(c - 5, Y0 + LATO_B - 1.2); ctx.quadraticCurveTo(c - 1.2, Y0 + LATO_B + 2, c, PUNTA)
  ctx.quadraticCurveTo(c + 1.2, Y0 + LATO_B + 2, c + 5, Y0 + LATO_B - 1.2); ctx.closePath()
}
function immagineBase(e: Ente, t: Tema, pr: number) {
  const { ctx } = tela(W_BASE, H_BASE, pr)
  const c = W_BASE / 2, cy = Y0 + LATO_B / 2, [alto, basso] = ENTI_BASI[e].grad
  ctx.beginPath(); ctx.ellipse(c, PUNTA + 1, 5.5, 1.8, 0, 0, Math.PI * 2) // ombra a terra
  ctx.fillStyle = t === 'scuro' ? 'rgba(0,0,0,.55)' : 'rgba(20,25,40,.22)'; ctx.filter = 'blur(.8px)'; ctx.fill(); ctx.filter = 'none'
  formaBase(ctx)
  ctx.save(); ctx.shadowColor = alfa(basso, t === 'scuro' ? 0.75 : 0.45); ctx.shadowBlur = 8; ctx.shadowOffsetY = 2.5
  ctx.fillStyle = basso; ctx.fill(); ctx.restore()
  const g = ctx.createLinearGradient(0, Y0, 0, PUNTA); g.addColorStop(0, alto); g.addColorStop(1, basso)
  ctx.fillStyle = g; ctx.fill()
  // vetro: riflesso in alto e bordo interno chiaro che sfuma verso il basso
  ctx.save(); ctx.clip()
  const lu = ctx.createLinearGradient(0, Y0, 0, cy); lu.addColorStop(0, 'rgba(255,255,255,.28)'); lu.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = lu; ctx.fillRect(0, Y0, W_BASE, LATO_B / 2)
  const bo = ctx.createLinearGradient(0, Y0, 0, PUNTA); bo.addColorStop(0, 'rgba(255,255,255,.75)'); bo.addColorStop(0.6, 'rgba(255,255,255,.15)'); bo.addColorStop(1, 'rgba(255,255,255,.05)')
  formaBase(ctx); ctx.strokeStyle = bo; ctx.lineWidth = 2; ctx.stroke()
  ctx.restore()
  // glifo bianco pieno al centro
  ctx.save(); ctx.fillStyle = '#fff'; ctx.strokeStyle = '#fff'; ctx.shadowColor = 'rgba(0,0,0,.18)'; ctx.shadowBlur = 1.5; ctx.shadowOffsetY = 0.6
  if (e === 'AIB') {
    ctx.font = '800 17px "Inter", "SF Pro Display", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText('H', c, cy + 1)
  } else {
    const s = 15 / 24; ctx.translate(c - 12 * s, cy - 12 * s); ctx.scale(s, s); ctx.lineWidth = 2.2
    disegnaIcona(ctx, e === 'VVF' ? Flame : TreePine, true)
  }
  ctx.restore()
  return ctx.getImageData(0, 0, W_BASE * pr, H_BASE * pr)
}

// stesse figure come data URL, per legenda e popup (componente funzionale <img>)
const urlCache = new Map<string, string>()
function dataUrl(chiave: string, img: () => ImageData) {
  if (!urlCache.has(chiave)) {
    const d = img(), cv = document.createElement('canvas'); cv.width = d.width; cv.height = d.height
    cv.getContext('2d')!.putImageData(d, 0, 0); urlCache.set(chiave, cv.toDataURL())
  }
  return urlCache.get(chiave)!
}
export const urlBase = (e: string, t: Tema) => dataUrl(`b${e}${t}`, () => immagineBase(e as Ente, t, 2))
export const urlMezzo = (f: Famiglia, colore: string, t: Tema) => dataUrl(`m${f}${colore}${t}`, () => immagineMezzo(f, colore, t, 2))
export const iconaImg = (src: string): Component => () => h('img', { src, alt: '', class: 'size-full object-contain' })

export function registraMezzi(m: MappaLibre, t: Tema) {
  const pr = Math.max(2, Math.ceil(window.devicePixelRatio || 1))
  const metti = (id: string, img: ImageData) => { if (m.hasImage(id)) m.removeImage(id); m.addImage(id, img, { pixelRatio: pr }) }
  for (const f of Object.keys(FAMIGLIE) as Famiglia[]) {
    for (const s of STATI_MEZZO) metti(`mezzo-${f}-${s.id}`, immagineMezzo(f, s.colore(t), t, pr, s.id === 'posto'))
    metti(`ombra-${f}`, immagineOmbra(f, t, pr))
  }
  for (const e of Object.keys(ENTI_BASI) as Ente[]) metti(`base-${e}`, immagineBase(e, t, pr))
}

export function aggiungiOperativo(m: MappaLibre, t: Tema, basi: any, flotta: any, scie: any, vis: { basi: boolean; terra: boolean; aerei: boolean }) {
  if (m.getSource('basi')) return
  const v = (b: boolean) => (b ? 'visible' : 'none')
  registraMezzi(m, t)
  m.addSource('basi', { type: 'geojson', data: basi })
  m.addLayer({ id: 'basi', type: 'symbol', source: 'basi', layout: {
    visibility: v(vis.basi), 'icon-image': ['concat', 'base-', ['get', 'ente']] as any, 'icon-anchor': 'bottom',
    'icon-size': ['interpolate', ['linear'], ['zoom'], 7, 0.6, 10, 0.8, 14, 1] as any, 'icon-allow-overlap': true, 'icon-ignore-placement': true,
    'icon-offset': [0, -4], 'symbol-sort-key': ['match', ['get', 'ente'], 'AIB', 3, 'VVF', 2, 1] as any, // un filo sopra i mezzi in base
  } })
  m.addSource('flotta-scie', { type: 'geojson', data: scie })
  m.addLayer({ id: 'flotta-scia', type: 'line', source: 'flotta-scie', layout: { visibility: v(vis.aerei), 'line-cap': 'round' }, paint: {
    'line-color': coloriMappa(t).testo, 'line-width': ['interpolate', ['linear'], ['zoom'], 7, 1.6, 12, 2.6] as any, 'line-opacity': 0.7, 'line-dasharray': [1, 1.6] } })
  m.addSource('flotta', { type: 'geojson', data: flotta })
  // aerei piu' grandi dei mezzi di terra: si leggono come "sopra" la mappa
  const dim = ['interpolate', ['linear'], ['zoom'], 7, ['case', ['==', ['get', 'categoria'], 'aereo'], 0.68, 0.52], 11, ['case', ['==', ['get', 'categoria'], 'aereo'], 0.88, 0.74], 14, ['case', ['==', ['get', 'categoria'], 'aereo'], 1.05, 0.92]]
  const ordine = ['match', ['get', 'colore'], 'posto', 4, 'mov', 3, 'acqua', 2, 'pattuglia', 1, 0] as any
  const comuni = { 'icon-allow-overlap': true, 'icon-ignore-placement': true, 'icon-rotation-alignment': 'map' as const,
    'icon-size': dim as any, 'icon-rotate': ['get', 'rotta'] as any, 'symbol-sort-key': ordine }
  m.addLayer({ id: 'flotta-ombra', type: 'symbol', source: 'flotta', filter: ['==', ['get', 'categoria'], 'aereo'], layout: {
    ...comuni, visibility: v(vis.aerei), 'icon-image': ['concat', 'ombra-', ['get', 'famiglia']] as any,
  }, paint: { 'icon-translate': [6, 9], 'icon-translate-anchor': 'viewport' } })
  m.addLayer({ id: 'flotta-ombra-terra', type: 'symbol', source: 'flotta', filter: ['==', ['get', 'categoria'], 'terra'], layout: {
    ...comuni, visibility: v(vis.terra), 'icon-image': 'ombra-terra',
  }, paint: { 'icon-translate': [1, 1.5], 'icon-translate-anchor': 'viewport', 'icon-opacity': 0.8 } })
  m.addLayer({ id: 'flotta-terra', type: 'symbol', source: 'flotta', filter: ['==', ['get', 'categoria'], 'terra'], layout: {
    ...comuni, visibility: v(vis.terra), 'icon-image': ['get', 'img'] as any } })
  m.addLayer({ id: 'flotta-aerei', type: 'symbol', source: 'flotta', filter: ['==', ['get', 'categoria'], 'aereo'], layout: {
    ...comuni, visibility: v(vis.aerei), 'icon-image': ['get', 'img'] as any } })
  impostaVisOperativo(m, vis)
}
export function impostaVisOperativo(m: MappaLibre | null, vis: { basi: boolean; terra: boolean; aerei: boolean }) {
  if (!m?.getLayer('basi')) return
  const v = (b: boolean) => (b ? 'visible' : 'none')
  m.setLayoutProperty('basi', 'visibility', v(vis.basi))
  for (const l of ['flotta-terra', 'flotta-ombra-terra']) m.setLayoutProperty(l, 'visibility', v(vis.terra))
  for (const l of ['flotta-aerei', 'flotta-ombra', 'flotta-scia']) m.setLayoutProperty(l, 'visibility', v(vis.aerei))
}
