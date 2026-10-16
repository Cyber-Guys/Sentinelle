import maplibregl, { type Map as MappaLibre, type StyleSpecification } from 'maplibre-gl'
import { layers, namedFlavor } from '@protomaps/basemaps'
import { Protocol } from 'pmtiles'
import { h, render, type Component } from 'vue'
import { Cloud, Flame, Grape, House, MapPin } from '@lucide/vue'
import IconaTerreno from '~/components/IconaTerreno.vue'

// Due viste. "mappa": Protomaps tutta in locale (tile e font serviti dal nostro nginx, niente rete), chiara e
// leggibile al sole, colori del flavor ritoccati sui token di tema.css, POI tolti, etichette in italiano.
// "satellite": immagini Esri World Imagery (serve rete) con sopra le sole etichette della mappa locale, in bianco.
// Le due viste convivono nello stesso stile: si passa dall'una all'altra senza ricaricare (impostaVista).
export type Vista = 'satellite' | 'mappa'

let pmtilesOk = false
export function registraPmtiles() {
  if (pmtilesOk) return
  maplibregl.addProtocol('pmtiles', new Protocol().tile)
  pmtilesOk = true
}

const BASE = namedFlavor('light')
const RITOCCHI = {
  background: '#bcd0e6', water: '#bcd0e6', earth: '#e8ecf0', buildings: '#cdd5de',
  landcover: { ...BASE.landcover, grassland: '#e2eadc', barren: '#e9e6df', urban_area: '#e1e6ec', farmland: '#e6ebdb', scrub: '#dfe8d5', forest: '#d3e2ca' },
  park_a: '#d5e5cf', park_b: '#d5e5cf', wood_a: '#d3e2ca', wood_b: '#d3e2ca', scrub_a: '#dfe8d5', scrub_b: '#dfe8d5',
  hospital: '#f0e0e0', industrial: '#dde2e8', school: '#e8e3d8', pedestrian: '#eef1f5', sand: '#efe9d8', beach: '#f1ebda',
  highway: '#ffffff', major: '#ffffff', link: '#ffffff', minor_a: '#ffffff', minor_b: '#ffffff', minor_service: '#f6f8fa', other: '#f6f8fa',
  highway_casing_early: '#9aa6b3', highway_casing_late: '#9aa6b3', major_casing_early: '#adb7c2', major_casing_late: '#adb7c2',
  link_casing: '#adb7c2', minor_casing: '#c2cad3', minor_service_casing: '#d0d6dd',
  bridges_highway: '#ffffff', bridges_major: '#ffffff', bridges_link: '#ffffff', bridges_minor: '#ffffff', bridges_other: '#f6f8fa',
  bridges_highway_casing: '#9aa6b3', bridges_major_casing: '#adb7c2', bridges_link_casing: '#adb7c2', bridges_minor_casing: '#c2cad3', bridges_other_casing: '#d0d6dd',
  tunnel_highway: '#d9dee4', tunnel_major: '#d9dee4', tunnel_link: '#d9dee4', tunnel_minor: '#e2e6ea', tunnel_other: '#e2e6ea',
  railway: '#a9b3bf', boundaries: '#97a2b0',
  city_label: '#1d2733', city_label_halo: '#f4f6f8', subplace_label: '#566170', subplace_label_halo: '#f4f6f8',
  roads_label_major: '#4a5563', roads_label_major_halo: '#f4f6f8', roads_label_minor: '#566170', roads_label_minor_halo: '#f4f6f8',
  ocean_label: '#5a7ea6', state_label: '#7b8696', state_label_halo: '#f4f6f8', country_label: '#7b8696',
  address_label: '#7b8696', address_label_halo: '#f4f6f8',
}
// etichette sul satellite: bianche con alone scuro
const SCURO = 'rgba(8, 12, 20, 0.78)'
const ETICHETTE_SATELLITE = {
  city_label: '#ffffff', city_label_halo: SCURO, subplace_label: '#f1f4f8', subplace_label_halo: SCURO,
  roads_label_major: '#ffffff', roads_label_major_halo: SCURO, roads_label_minor: '#e9edf3', roads_label_minor_halo: SCURO,
  ocean_label: '#cfe0f3', state_label: '#e1e7ef', state_label_halo: SCURO, country_label: '#e1e7ef',
  address_label: '#e9edf3', address_label_halo: SCURO,
}

const SATELLITE = {
  tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
  tileSize: 256, maxzoom: 19,
}

const senzaPoi = (l: any) => !String(l.id).startsWith('pois')
const conVisibilita = (l: any, visibile: boolean) => ({ ...l, layout: { ...(l.layout ?? {}), visibility: visibile ? 'visible' : 'none' } })

export function stileMappa(vista: Vista = 'mappa'): StyleSpecification {
  const origine = typeof location !== 'undefined' ? location.origin : ''
  const sat = vista === 'satellite'
  const base = (layers('protomaps', { ...BASE, ...RITOCCHI } as any, { lang: 'it' }) as any[]).filter(senzaPoi).map((l) => conVisibilita(l, !sat))
  const etichette = (layers('protomaps', { ...BASE, ...RITOCCHI, ...ETICHETTE_SATELLITE } as any, { lang: 'it' }) as any[])
    .filter((l) => l.type === 'symbol' && senzaPoi(l))
    .map((l) => conVisibilita({ ...l, id: `sat-${l.id}` }, sat))
  return {
    version: 8,
    glyphs: `${origine}/basemap/fonts/{fontstack}/{range}.pbf`,
    sprite: `${origine}/basemap/sprites/light`,
    sources: {
      protomaps: { type: 'vector', url: 'pmtiles:///tiles/sardegna.pmtiles' },
      satellite: { type: 'raster', ...SATELLITE },
    },
    layers: [...base, conVisibilita({ id: 'satellite', type: 'raster', source: 'satellite', paint: { 'raster-fade-duration': 200 } }, sat), ...etichette],
  }
}

/** Passa da una vista all'altra: i livelli di base e del satellite si accendono a turno, i nostri (zone, cerchi) restano. */
export function impostaVista(m: MappaLibre, vista: Vista) {
  const sat = vista === 'satellite'
  for (const l of m.getStyle().layers as any[]) {
    const delSatellite = l.id === 'satellite' || String(l.id).startsWith('sat-')
    const base = l.type === 'background' || l.source === 'protomaps'
    if (!delSatellite && !base) continue
    m.setLayoutProperty(l.id, 'visibility', delSatellite === sat ? 'visible' : 'none')
  }
}

// estratto della mappa: oltre c'e' solo mare aperto
export const LIMITI: [[number, number], [number, number]] = [[5.6, 38.77], [12.3, 41.33]]
export const LOCALE_MAPPA = { 'Popup.Close': 'Chiudi' }

// --- geometrie ---------------------------------------------------------------------------------------

const R = 6371008.8
const rad = (g: number) => (g * Math.PI) / 180

export function destino(lat: number, lon: number, gradi: number, metri: number): [number, number] {
  const d = metri / R, b = rad(gradi), p1 = rad(lat), l1 = rad(lon)
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b))
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2))
  return [(l2 * 180) / Math.PI, (p2 * 180) / Math.PI]
}

export function cerchio(lat: number, lon: number, raggioM: number, n = 48): GeoJSON.Feature<GeoJSON.Polygon> {
  const anello = Array.from({ length: n + 1 }, (_, i) => destino(lat, lon, (360 / n) * i, raggioM))
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [anello] } }
}

/** Direzione (gradi dal nord) dal punto `da` al punto `a`. */
export function direzioneVerso(da: { lat: number; lon: number }, a: { lat: number; lon: number }): number {
  const y = Math.sin(rad(a.lon - da.lon)) * Math.cos(rad(a.lat))
  const x = Math.cos(rad(da.lat)) * Math.sin(rad(a.lat)) - Math.sin(rad(da.lat)) * Math.cos(rad(a.lat)) * Math.cos(rad(a.lon - da.lon))
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360
}

const vuoto = (): GeoJSON.FeatureCollection => ({ type: 'FeatureCollection', features: [] })

// --- la mia posizione --------------------------------------------------------------------------------
// Cerchio di precisione: livello geografico (cresce e cala con lo zoom, ed e' giusto cosi').
// Punto e fascio dello sguardo: marcatore HTML a misura fissa in pixel, che ruota con la direzione:
// il fascio sfuma verso l'esterno (come Apple Maps) e non cambia con lo zoom.

export function preparaPosizione(m: MappaLibre) {
  if (m.getSource('io-precisione')) return
  m.addSource('io-precisione', { type: 'geojson', data: vuoto() })
  m.addLayer({ id: 'io-precisione', type: 'fill', source: 'io-precisione', paint: { 'fill-color': '#4f8cff', 'fill-opacity': 0.16 } })
}

export interface MarcatoreIo { aggiorna: (pos: { lat: number; lon: number; precisione: number }, dir: number | null) => void; rimuovi: () => void }

export function creaMarcatoreIo(m: MappaLibre): MarcatoreIo {
  const el = document.createElement('div')
  el.className = 'io io-senza-cono'
  el.innerHTML = '<div class="io-cono"></div><div class="io-punto"></div>'
  const marker = new maplibregl.Marker({ element: el, rotationAlignment: 'map', pitchAlignment: 'map' }).setLngLat([0, 0]).addTo(m)
  return {
    aggiorna(pos, dir) {
      marker.setLngLat([pos.lon, pos.lat])
      el.classList.toggle('io-senza-cono', dir === null)
      marker.setRotation(dir ?? 0)
      ;(m.getSource('io-precisione') as maplibregl.GeoJSONSource | undefined)?.setData((pos.precisione > 15 ? cerchio(pos.lat, pos.lon, Math.min(pos.precisione, 500)) : vuoto()) as any)
    },
    rimuovi: () => marker.remove(),
  }
}

// --- zone a rischio ----------------------------------------------------------------------------------

export function impostaZone(m: MappaLibre, id: string, dati: GeoJSON.FeatureCollection) {
  const sorgente = m.getSource(`zone-${id}`) as maplibregl.GeoJSONSource | undefined
  if (sorgente) { sorgente.setData(dati); return }
  m.addSource(`zone-${id}`, { type: 'geojson', data: dati })
  const colore = ['match', ['get', 'livello'], 'molto alto', '#c4360f', 'alto', '#c4360f', '#d99a1e']
  m.addLayer({ id: `zone-${id}`, type: 'fill', source: `zone-${id}`, paint: { 'fill-color': colore as any, 'fill-opacity': 0.3 } }, m.getLayer('io-precisione') ? 'io-precisione' : undefined)
  m.addLayer({ id: `zone-${id}-bordo`, type: 'line', source: `zone-${id}`, paint: { 'line-color': colore as any, 'line-width': 1.6, 'line-opacity': 0.8 } })
}

export function mostraZone(m: MappaLibre, id: string, visibile: boolean) {
  for (const l of [`zone-${id}`, `zone-${id}-bordo`]) if (m.getLayer(l)) m.setLayoutProperty(l, 'visibility', visibile ? 'visible' : 'none')
}

// --- cerchio attorno a ogni segnalazione attiva ------------------------------------------------------
// Raggio indicativo: l'incendio e' un punto, il fumo si vede da lontano, il terreno a rischio e' un'area piccola.
const RAGGIO_INCIDENTE: Record<TipoSegnalazione, number> = { fuoco: 350, fumo: 600, area_a_rischio: 200 }

export function impostaIncidenti(m: MappaLibre, lista: { tipo: TipoSegnalazione; lat: number; lon: number; stato_ufficiale: string }[]) {
  const dati: GeoJSON.FeatureCollection = {
    type: 'FeatureCollection',
    features: lista.filter((c) => c.stato_ufficiale !== 'spento').map((c) => ({ ...cerchio(c.lat, c.lon, RAGGIO_INCIDENTE[c.tipo], 40), properties: { tipo: c.tipo } })),
  }
  const sorgente = m.getSource('incidenti') as maplibregl.GeoJSONSource | undefined
  if (sorgente) { sorgente.setData(dati); return }
  m.addSource('incidenti', { type: 'geojson', data: dati })
  const colore = ['match', ['get', 'tipo'], 'fuoco', '#c4360f', 'fumo', '#566170', '#8a5a2b']
  const prima = m.getLayer('io-precisione') ? 'io-precisione' : undefined
  m.addLayer({ id: 'incidenti', type: 'fill', source: 'incidenti', paint: { 'fill-color': colore as any, 'fill-opacity': 0.26 } }, prima)
  m.addLayer({ id: 'incidenti-alone', type: 'line', source: 'incidenti', paint: { 'line-color': '#ffffff', 'line-width': 4.5, 'line-opacity': 0.55 } }, prima)
  m.addLayer({ id: 'incidenti-bordo', type: 'line', source: 'incidenti', paint: { 'line-color': colore as any, 'line-width': 2, 'line-opacity': 0.9 } }, prima)
}

// --- pin HTML ----------------------------------------------------------------------------------------

type Icona = TipoSegnalazione | TipoLocalita

const ICONE: Record<Icona, Component> = { fuoco: Flame, fumo: Cloud, area_a_rischio: IconaTerreno, terreno: IconaTerreno, casa: House, vigna: Grape, altro: MapPin }

export interface OpzioniPin { icona?: Icona; classe?: string; testo?: string; etichetta?: string; onda?: boolean; nome?: string; conteggio?: number; alTocco?: () => void }

export function creaPin(o: OpzioniPin): HTMLElement {
  const el = document.createElement('div')
  el.className = ['pin', o.icona ? `pin-${o.icona === 'terreno' || o.icona === 'vigna' || o.icona === 'altro' ? 'casa' : o.icona}` : '', o.classe ?? '', o.onda ? 'pin-onda' : ''].join(' ').trim()
  if (o.testo) el.textContent = o.testo
  else if (o.icona) {
    const c = document.createElement('span')
    c.style.display = 'contents'
    render(h(ICONE[o.icona]), c)
    el.appendChild(c)
  }
  if (o.etichetta) {
    const t = document.createElement('span')
    t.className = 'pin-etichetta'
    t.textContent = o.etichetta
    el.appendChild(t)
  }
  if (o.conteggio && o.conteggio > 1) {
    const c = document.createElement('span')
    c.className = 'pin-conteggio'
    c.textContent = String(o.conteggio)
    el.appendChild(c)
  }
  if (o.alTocco) {
    el.setAttribute('role', 'button')
    el.tabIndex = 0
    if (o.nome) el.setAttribute('aria-label', o.nome)
    el.addEventListener('click', (e) => { e.stopPropagation(); o.alTocco!() })
    el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); o.alTocco!() } })
    el.style.cursor = 'pointer'
  }
  return el
}

export function mettiPin(m: MappaLibre, lat: number, lon: number, o: OpzioniPin): maplibregl.Marker {
  return new maplibregl.Marker({ element: creaPin(o), anchor: 'center' }).setLngLat([lon, lat]).addTo(m)
}

// --- raggruppamento ----------------------------------------------------------------------------------

/** Quanto e' pericolosa una segnalazione: fuoco > fumo > terreno a rischio; quelle gia' spente per ultime. */
export const gravita = (c: { tipo: TipoSegnalazione; stato_ufficiale: string }) =>
  (c.stato_ufficiale === 'spento' ? 0 : 10) + (c.tipo === 'fuoco' ? 3 : c.tipo === 'fumo' ? 2 : 1)

export interface Gruppo<T> { principale: T; membri: T[] }

/** Segnalazioni vicine sullo schermo (meno di `raggioPx`) diventano un solo gruppo, rappresentato dalla piu' pericolosa. */
export function raggruppa<T extends { tipo: TipoSegnalazione; stato_ufficiale: string; lat: number; lon: number; creata_il: string }>(m: MappaLibre, lista: T[], raggioPx = 44): Gruppo<T>[] {
  const punti = [...lista]
    .sort((a, b) => gravita(b) - gravita(a) || b.creata_il.localeCompare(a.creata_il))
    .map((c) => ({ c, p: m.project([c.lon, c.lat]) }))
  const presi = new Set<T>()
  const out: Gruppo<T>[] = []
  for (const a of punti) {
    if (presi.has(a.c)) continue
    presi.add(a.c)
    const membri = [a.c]
    for (const b of punti) {
      if (presi.has(b.c)) continue
      if (Math.hypot(a.p.x - b.p.x, a.p.y - b.p.y) < raggioPx) { presi.add(b.c); membri.push(b.c) }
    }
    out.push({ principale: a.c, membri })
  }
  return out
}

/** Inquadra un insieme di punti lasciando spazio ai bordi (il margine vale solo per il calcolo: la mappa non resta "imbottita"). */
export function inquadra(m: MappaLibre, punti: { lat: number; lon: number }[], opz: { margine?: number | maplibregl.PaddingOptions; zoomMax?: number } = {}) {
  if (!punti.length) return
  if (punti.length === 1) { m.easeTo({ center: [punti[0]!.lon, punti[0]!.lat], zoom: opz.zoomMax ?? 14, duration: 500 }); return }
  const b = new maplibregl.LngLatBounds()
  for (const p of punti) b.extend([p.lon, p.lat])
  const cam = m.cameraForBounds(b, { padding: opz.margine ?? 60, maxZoom: opz.zoomMax ?? 14 })
  if (cam) m.easeTo({ center: cam.center, zoom: cam.zoom, duration: 600 })
}

/** Vista che contiene per intero i cerchi di una o piu' segnalazioni e, se serve, un altro punto (di solito io). */
export function cameraCerchi(m: MappaLibre, cerchi: { lat: number; lon: number; tipo?: TipoSegnalazione }[], margine: maplibregl.PaddingOptions, anche?: { lat: number; lon: number }, zoomMax = 16.5) {
  const b = new maplibregl.LngLatBounds()
  for (const c of cerchi) for (const [lon, lat] of cerchio(c.lat, c.lon, RAGGIO_INCIDENTE[c.tipo ?? 'fumo'], 24).geometry.coordinates[0]!) b.extend([lon, lat])
  if (anche) b.extend([anche.lon, anche.lat])
  return m.cameraForBounds(b, { padding: margine, maxZoom: zoomMax })
}
