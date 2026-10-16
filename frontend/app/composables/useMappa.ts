import maplibregl, { type Map as MappaLibre, type StyleSpecification } from 'maplibre-gl'
import { layers, namedFlavor } from '@protomaps/basemaps'
import { Protocol } from 'pmtiles'
import type { Tema } from './useTema'
import { h, render, type Component } from 'vue'
import type { Segnalazione } from './useApi'
import PopupIncendio from '~/components/PopupIncendio.vue'
import PopupHotspot from '~/components/PopupHotspot.vue'

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
export function clicIncendio(m: MappaLibre, pin: string[], bloccato: () => boolean = () => false) {
  m.on('click', 'storico-riempimento', (ev) => {
    const p = ev.features?.[0]?.properties
    if (!p || bloccato()) return
    const layers = pin.filter((l) => m.getLayer(l))
    if (layers.length && m.queryRenderedFeatures(ev.point, { layers }).length) return
    apriPopup(m, ev.lngLat, PopupIncendio, { anno: Number(p.anno), data: p.data, comune: p.comune ? String(p.comune) : undefined, ettari: p.ettari != null ? Number(p.ettari) : null, bosco: p.bosco_ha != null ? Number(p.bosco_ha) : null })
  })
}

// Tocco su un hotspot satellitare: popup informativo; `pin` (segnalazioni) vince, l'hotspot vince su storico e mappature.
// `simula` (cruscotto): il popup mostra "Simula scenario" e lo avvia dal punto dell'hotspot.
export function clicHotspot(m: MappaLibre, pin: string[], bloccato: () => boolean = () => false, simula?: (lat: number, lon: number, titolo: string) => void) {
  m.on('click', 'hotspot', (ev) => {
    const f = ev.features?.[0]
    if (!f || bloccato()) return
    const layers = pin.filter((l) => m.getLayer(l))
    if (layers.length && m.queryRenderedFeatures(ev.point, { layers }).length) return
    const p = f.properties ?? {}
    const n = (v: unknown) => (v == null || v === 'null' || v === '' ? null : Number(v))
    const [lon, lat] = (f.geometry as any).coordinates
    apriPopup(m, [lon, lat], PopupHotspot, {
      lat, lon, rilevato_il: p.rilevato_il, confidenza: p.confidenza, comune: p.comune && p.comune !== 'null' ? String(p.comune) : null,
      frp: n(p.frp), luminosita: n(p.luminosita), satellite: p.satellite && p.satellite !== 'null' ? String(p.satellite) : null,
      giorno: p.giorno == null || p.giorno === 'null' ? null : p.giorno === true || p.giorno === 'true',
      onSimula: simula ? () => { chiudiPopup(); simula(lat, lon, p.comune && p.comune !== 'null' ? String(p.comune) : '') } : undefined,
    })
  })
  m.on('mouseenter', 'hotspot', () => (m.getCanvas().style.cursor = 'pointer'))
  m.on('mouseleave', 'hotspot', () => (m.getCanvas().style.cursor = ''))
}

/*
  Segnaposto a icona (mappature dei cittadini): badge tondo di vetro scuro (chiaro nel tema chiaro),
  anello sottile e icona Lucide nel colore del tipo, punta minima sul punto, ombra appena accennata.
  Disegnati in modo sincrono su canvas (icona Lucide renderizzata in un div e ridisegnata con Path2D),
  cosi' l'immagine esiste prima del layer e `styleimagemissing` puo' rigenerarla al volo.
  Registrare con registraSegnaposti() a ogni style.load (setStyle cancella le immagini).
*/
export type Segnaposto = { id: string; icona: Component; colore: string }
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

function disegnaIcona(ctx: CanvasRenderingContext2D, icona: Component) {
  const el = document.createElement('div')
  render(h(icona as any), el)
  for (const n of Array.from(el.querySelectorAll('svg > *'))) {
    const a = (k: string) => Number(n.getAttribute(k) ?? 0)
    if (n.tagName === 'path') { ctx.stroke(new Path2D(n.getAttribute('d') ?? '')); continue }
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
  ctx.fillStyle = toniMappature(tema).vetro
  ctx.fill()
  ctx.restore()
  ctx.lineWidth = 1.5; ctx.lineJoin = 'round'
  ctx.strokeStyle = s.colore
  ctx.stroke()
  // icona 24x24 Lucide ridotta a 13 px, tratto nel colore del tipo
  ctx.save()
  ctx.translate(cx - 6.5, CY - 6.5); ctx.scale(13 / 24, 13 / 24)
  ctx.strokeStyle = s.colore; ctx.lineWidth = 2.3; ctx.lineCap = 'round'; ctx.lineJoin = 'round'
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
  acqua: { nome: string; tipo: string; distanza_km: number; lat: number; lon: number }[]
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
