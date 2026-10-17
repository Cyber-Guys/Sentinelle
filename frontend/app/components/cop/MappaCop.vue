<script setup lang="ts">
import maplibregl, { type Map as MappaLibre, type GeoJSONSource } from 'maplibre-gl'
import { h } from 'vue'
import { Binoculars, FlameKindling, Truck, Plane, Building2 } from '@lucide/vue'
import {
  stileMappa, registraPmtiles, LOCALE_MAPPA, animaAloni, apriPopup, chiudiPopup, aggiungiStoricoIncendi, aggiungiInvasi, impostaInvasi,
  clicInvasi, registraSegnaposti, aggiungiOperativo, impostaVisOperativo, registraMezzi, statoMezzo, famigliaMezzo, ENTI_BASI, FAMIGLIE,
  coloriMappa, type Alone, type Segnaposto,
} from '~/composables/useMappa'
import PopupMappa from '~/components/PopupMappa.vue'
import { coloriAllerta, cerchio, maschera, type AreaCop, type Bollettino } from '~/composables/useCop'

/*
  Mappa della dashboard COP. Una sola istanza per ingresso e area: la scelta dell'area e' uno zoom animato
  sulla stessa carta (il momento "wow" della demo), con una maschera che scurisce il resto dell'isola.
  Tutti i livelli si ricreano a ogni `style.load` (cambio tema = setStyle).
*/
export type Livelli = {
  rischio: boolean; incendi: boolean; spenti: boolean; storico: boolean; invasi: boolean; fuochi: boolean
  vedette: boolean; basi: boolean; terra: boolean; aerei: boolean; segnalazioni: boolean
}
const props = defineProps<{
  aree: AreaCop[]; areaSel: string | null; areaHover: string | null; bollettino: Bollettino | null; livelli: Livelli
  anni: [number, number]; incendi: any; vedette: any; fuochi: any; invasi: any; basi: any; flotta: any[]
  segnalazioni: { id: number; lat: number; lon: number; priorita: number }[]; incendioSel: string | null; padDestra: number
}>()
const emit = defineEmits<{ scegli: [id: string]; hover: [id: string | null]; incendio: [id: string]; segnalazione: [id: number] }>()

const { tema } = useTema()
const contenitore = ref<HTMLElement>()
let mappa: MappaLibre | null = null
let fermaAloni = () => {}
const VUOTO = { type: 'FeatureCollection', features: [] as any[] }
const ISOLA: [number, number, number, number] = [8.1, 38.84, 9.85, 41.32]
const vis = (b: boolean) => (b ? 'visible' : 'none')

const tinte = () => {
  const s = tema.value === 'scuro'
  return { cielo: s ? '#5aa9e6' : '#2f7fc0', viola: s ? '#b48cf2' : '#6a46a6', fondo: s ? '#05070b' : '#f6f4ef', linea: s ? '#f3f1ec' : '#1a1a17', grigio: s ? '#8a867e' : '#6d6960' }
}
const segnaposti = (): Segnaposto[] => [
  { id: 'cop-vedetta', icona: Binoculars, colore: tinte().cielo },
  { id: 'cop-fuoco-aut', icona: FlameKindling, colore: tinte().viola },
]

// ---------------------------------------------------------------- dati derivati

const fcAree = computed(() => ({ type: 'FeatureCollection', features: props.aree.map((a) => ({ type: 'Feature', id: a.id, geometry: a.geometria, properties: { id: a.id, nome: a.nome } })) }))
const fcSedi = computed(() => ({ type: 'FeatureCollection', features: props.aree.map((a) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [(a.bbox[0] + a.bbox[2]) / 2, (a.bbox[1] + a.bbox[3]) / 2] }, properties: { id: a.id, nome: a.nome.toUpperCase() } })) }))
const fcMaschera = computed(() => {
  const a = props.aree.find((x) => x.id === props.areaSel)
  return a ? { type: 'FeatureCollection', features: [maschera(a.geometria)] } : VUOTO
})
const fcRaggi = computed(() => ({ type: 'FeatureCollection', features: (props.vedette?.features ?? []).map((f: any) => ({ type: 'Feature', geometry: cerchio(f.geometry.coordinates, f.properties.raggio_km), properties: f.properties })) }))
const fcCentri = computed(() => ({ type: 'FeatureCollection', features: (props.incendi?.features ?? []).map((f: any) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: f.properties.centro }, properties: { ...f.properties, sel: f.properties.id === props.incendioSel } })) }))
const fcSegn = computed(() => ({ type: 'FeatureCollection', features: props.segnalazioni.map((s) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [s.lon, s.lat] }, properties: { id: s.id, priorita: s.priorita } })) }))
const fcFlotta = computed(() => ({ type: 'FeatureCollection', features: props.flotta.map((x) => {
  const st = statoMezzo(x.stato), fam = famigliaMezzo(x)
  return { type: 'Feature', geometry: { type: 'Point', coordinates: [x.lon, x.lat] }, properties: { ...x, famiglia: fam, colore: st.id, img: `mezzo-${fam}-${st.id}` } }
}) }))

// ---------------------------------------------------------------- livelli

function aggiungiLivelli(m: MappaLibre) {
  const t = tema.value, c = coloriMappa(t), all = coloriAllerta(t), ti = tinte()
  registraSegnaposti(m, segnaposti(), t)
  registraMezzi(m, t)

  aggiungiStoricoIncendi(m, c, 'tutti', props.livelli.storico)
  filtraStorico(m)

  // Bollettino CFD: tre fill annidati con un bordo sfumato (line-blur) che rende morbide le zone
  m.addSource('cfd', { type: 'geojson', data: props.bollettino?.zone ?? VUOTO })
  const colore = ['match', ['get', 'livello'], 'rosso', all.rosso, 'arancione', all.arancione, all.verde] as any
  const scuro = t === 'scuro'
  m.addLayer({ id: 'cfd-fill', type: 'fill', source: 'cfd', layout: { visibility: vis(props.livelli.rischio) }, paint: {
    'fill-color': colore, 'fill-opacity': ['match', ['get', 'livello'], 'rosso', scuro ? 0.26 : 0.24, 'arancione', scuro ? 0.17 : 0.18, scuro ? 0.06 : 0.08] as any,
    'fill-opacity-transition': { duration: 400 } } })
  m.addLayer({ id: 'cfd-alone', type: 'line', source: 'cfd', filter: ['!=', ['get', 'livello'], 'verde'], layout: { visibility: vis(props.livelli.rischio), 'line-join': 'round' }, paint: {
    'line-color': colore, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 8, 10, 22] as any, 'line-blur': ['interpolate', ['linear'], ['zoom'], 6, 8, 10, 20] as any, 'line-opacity': 0.32 } })
  m.addLayer({ id: 'cfd-bordo', type: 'line', source: 'cfd', filter: ['!=', ['get', 'livello'], 'verde'], layout: { visibility: vis(props.livelli.rischio), 'line-join': 'round' }, paint: {
    'line-color': colore, 'line-width': 1.1, 'line-opacity': 0.75 } })

  // Raggio d'azione delle vedette
  m.addSource('raggi', { type: 'geojson', data: fcRaggi.value })
  m.addLayer({ id: 'raggi-fill', type: 'fill', source: 'raggi', layout: { visibility: vis(props.livelli.vedette) }, paint: { 'fill-color': ti.cielo, 'fill-opacity': 0.045 } })
  m.addLayer({ id: 'raggi-linea', type: 'line', source: 'raggi', layout: { visibility: vis(props.livelli.vedette) }, paint: { 'line-color': ti.cielo, 'line-width': 1, 'line-opacity': 0.45, 'line-dasharray': [2, 2.5] } })

  // Aree COP: contorni, evidenza al passaggio, maschera fuori dall'area scelta
  m.addSource('aree', { type: 'geojson', data: fcAree.value as any, promoteId: 'id' })
  m.addLayer({ id: 'aree-fill', type: 'fill', source: 'aree', paint: {
    'fill-color': ti.linea, 'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.09, 0] as any, 'fill-opacity-transition': { duration: 180 } } })
  m.addSource('maschera', { type: 'geojson', data: fcMaschera.value as any })
  m.addLayer({ id: 'maschera', type: 'fill', source: 'maschera', paint: { 'fill-color': ti.fondo, 'fill-opacity': 0, 'fill-opacity-transition': { duration: 700 } } })
  m.addLayer({ id: 'aree-linea', type: 'line', source: 'aree', layout: { 'line-join': 'round' }, paint: {
    'line-color': ti.linea, 'line-opacity': ['case', ['boolean', ['feature-state', 'sel'], false], 0.9, ['boolean', ['feature-state', 'hover'], false], 0.75, 0.32] as any,
    'line-width': ['case', ['boolean', ['feature-state', 'sel'], false], 2, ['boolean', ['feature-state', 'hover'], false], 1.6, 1] as any } })

  // Incendi: area bruciata (attiva o spenta) + centro pulsante
  m.addSource('incendi', { type: 'geojson', data: props.incendi ?? VUOTO })
  const attivo = ['==', ['get', 'stato'], 'attivo'] as any
  m.addLayer({ id: 'incendi-fill', type: 'fill', source: 'incendi', paint: { 'fill-color': ['case', attivo, c.brace, ti.grigio] as any, 'fill-opacity': ['case', attivo, 0.34, 0.22] as any } })
  m.addLayer({ id: 'incendi-alone', type: 'line', source: 'incendi', filter: attivo, paint: { 'line-color': c.brace, 'line-width': 10, 'line-blur': 8, 'line-opacity': 0.55 } })
  m.addLayer({ id: 'incendi-linea', type: 'line', source: 'incendi', paint: { 'line-color': ['case', attivo, c.brace, ti.grigio] as any, 'line-width': ['case', attivo, 1.6, 1.2] as any, 'line-dasharray': [3, 2] } })
  m.addSource('centri', { type: 'geojson', data: fcCentri.value as any })
  m.addLayer({ id: 'centri-alone', type: 'circle', source: 'centri', filter: attivo, paint: { 'circle-color': c.brace, 'circle-radius': 14, 'circle-opacity': 0.3 } })
  m.addLayer({ id: 'centri', type: 'circle', source: 'centri', paint: {
    'circle-color': ['case', attivo, c.brace, ti.grigio] as any, 'circle-radius': ['case', ['get', 'sel'], 8, 5.5] as any,
    'circle-stroke-color': ['case', ['get', 'sel'], c.testo, c.bordo] as any, 'circle-stroke-width': ['case', ['get', 'sel'], 2.5, 1.5] as any } })
  m.addLayer({ id: 'centri-etichetta', type: 'symbol', source: 'centri', minzoom: 8.4, layout: {
    'text-field': ['get', 'nome'], 'text-font': ['Noto Sans Medium'], 'text-size': 11.5, 'text-anchor': 'top', 'text-offset': [0, 1.1], 'text-optional': true },
    paint: { 'text-color': ['case', attivo, c.testo, ti.grigio] as any, 'text-halo-color': ti.fondo, 'text-halo-width': 1.6 } })

  aggiungiInvasi(m, t, props.invasi ?? VUOTO, props.livelli.invasi)

  m.addSource('fuochi', { type: 'geojson', data: props.fuochi ?? VUOTO })
  m.addLayer({ id: 'fuochi', type: 'symbol', source: 'fuochi', layout: { visibility: vis(props.livelli.fuochi), 'icon-image': 'cop-fuoco-aut', 'icon-anchor': 'bottom',
    'icon-allow-overlap': true, 'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 11, 1] as any }, paint: { 'icon-opacity': ['match', ['get', 'stato'], 'Concluso', 0.5, 1] as any } })
  m.addSource('vedette', { type: 'geojson', data: props.vedette ?? VUOTO })
  m.addLayer({ id: 'vedette', type: 'symbol', source: 'vedette', layout: { visibility: vis(props.livelli.vedette), 'icon-image': 'cop-vedetta', 'icon-anchor': 'bottom',
    'icon-allow-overlap': true, 'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 11, 1] as any } })

  aggiungiOperativo(m, t, props.basi ?? VUOTO, fcFlotta.value, VUOTO, { basi: props.livelli.basi, terra: props.livelli.terra, aerei: props.livelli.aerei })

  // Segnalazioni da verificare: pin ambra con onda
  m.addSource('segn', { type: 'geojson', data: fcSegn.value as any })
  m.addLayer({ id: 'segn-alone', type: 'circle', source: 'segn', layout: { visibility: vis(props.livelli.segnalazioni) }, paint: { 'circle-color': c.ambra, 'circle-radius': 9, 'circle-opacity': 0.45 } })
  m.addLayer({ id: 'segn', type: 'circle', source: 'segn', layout: { visibility: vis(props.livelli.segnalazioni) }, paint: { 'circle-color': c.ambra, 'circle-radius': 6, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 1.5 } })

  // Nomi delle aree, solo all'ingresso
  m.addSource('sedi', { type: 'geojson', data: fcSedi.value as any })
  m.addLayer({ id: 'sedi', type: 'symbol', source: 'sedi', layout: { visibility: vis(!props.areaSel), 'text-field': ['get', 'nome'], 'text-font': ['Noto Sans Medium'],
    'text-size': 12, 'text-letter-spacing': 0.14, 'text-allow-overlap': true }, paint: { 'text-color': ti.linea, 'text-opacity': 0.82, 'text-halo-color': ti.fondo, 'text-halo-width': 1.4 } })

  aggiornaStatoAree(m)
  aggiornaMaschera(m, false)
  fermaAloni()
  const aloni: Alone[] = [
    { layer: 'centri-alone', periodo: 3200, da: 9, a: 22, opacita: 0.4, respiro: true },
    { layer: 'segn-alone', periodo: 2600, da: 7, a: 22, opacita: 0.5 },
  ]
  fermaAloni = animaAloni(m, aloni)
}

function filtraStorico(m: MappaLibre) {
  const f = ['all', ['>=', ['get', 'anno'], props.anni[0]], ['<=', ['get', 'anno'], props.anni[1]]] as any
  for (const id of ['storico-riempimento', 'storico-linea']) {
    if (!m.getLayer(id)) continue
    m.setFilter(id, f)
    m.setLayoutProperty(id, 'visibility', vis(props.livelli.storico))
  }
}

let hoverPrec: string | null = null
let selPrec: string | null = null
function aggiornaStatoAree(m: MappaLibre) {
  if (!m.getSource('aree')) return
  if (hoverPrec) m.setFeatureState({ source: 'aree', id: hoverPrec }, { hover: false })
  if (selPrec) m.setFeatureState({ source: 'aree', id: selPrec }, { sel: false })
  hoverPrec = props.areaSel ? null : props.areaHover
  selPrec = props.areaSel
  if (hoverPrec) m.setFeatureState({ source: 'aree', id: hoverPrec }, { hover: true })
  if (selPrec) m.setFeatureState({ source: 'aree', id: selPrec }, { sel: true })
}
function aggiornaMaschera(m: MappaLibre, anima = true) {
  if (!m.getLayer('maschera')) return
  ;(m.getSource('maschera') as GeoJSONSource).setData(fcMaschera.value as any)
  m.setPaintProperty('maschera', 'fill-opacity-transition', { duration: anima ? 700 : 0 })
  m.setPaintProperty('maschera', 'fill-opacity', props.areaSel ? (tema.value === 'scuro' ? 0.62 : 0.5) : 0)
  m.setLayoutProperty('sedi', 'visibility', vis(!props.areaSel))
  m.setLayoutProperty('aree-fill', 'visibility', vis(!props.areaSel))
}

// ---------------------------------------------------------------- camera

const riduciMoto = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches
const curva = (t: number) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2) // ease-in-out cubica
function inquadra(anima = true) {
  if (!mappa) return
  const a = props.aree.find((x) => x.id === props.areaSel)
  const largo = contenitore.value!.clientWidth
  const padding = a
    ? { top: 72, bottom: 40, left: largo > 900 ? 300 : 24, right: props.padDestra + 32 }
    : { top: 56, bottom: 48, left: largo > 900 ? 470 : 24, right: 56 }
  mappa.fitBounds((a?.bbox ?? ISOLA) as any, { padding, duration: anima && !riduciMoto() ? 1500 : 0, easing: curva, essential: true })
}
defineExpose({
  inquadra,
  volaA(c: [number, number], zoom = 12) { mappa?.flyTo({ center: c, zoom, duration: riduciMoto() ? 0 : 1100, easing: curva, essential: true, padding: { right: props.padDestra, top: 0, bottom: 0, left: 0 } }) },
})

// ---------------------------------------------------------------- popup

function popupSemplice(lngLat: any, icona: any, tinta: string, etichetta: string, titolo: string, sottotitolo: string, righe: [string, string][] = []) {
  if (!mappa) return
  apriPopup(mappa, lngLat, PopupMappa, { icona, tinta: [tinta, tinta], etichetta, titolo, sottotitolo }, () => righe.length
    ? h('dl', { class: 'popup-metriche mt-2.5 grid grid-cols-2 gap-x-3 gap-y-1.5 rounded-m p-2.5 text-[.76rem]' }, righe.flatMap(([k, v]) => [h('dt', { class: 'text-testo-3' }, k), h('dd', { class: 'cifre text-right font-medium' }, v)]))
    : null)
}

function eventi(m: MappaLibre) {
  const puntatore = (l: string) => {
    m.on('mouseenter', l, () => (m.getCanvas().style.cursor = 'pointer'))
    m.on('mouseleave', l, () => (m.getCanvas().style.cursor = ''))
  }
  // ingresso: passaggio e clic sulle aree
  m.on('mousemove', 'aree-fill', (e) => { if (!props.areaSel) emit('hover', String(e.features?.[0]?.properties?.id ?? '') || null) })
  m.on('mouseleave', 'aree-fill', () => { if (!props.areaSel) emit('hover', null) })
  m.on('click', 'aree-fill', (e) => { const id = e.features?.[0]?.properties?.id; if (!props.areaSel && id) emit('scegli', String(id)) })
  puntatore('aree-fill')

  for (const l of ['centri', 'incendi-fill']) {
    m.on('click', l, (e) => { if (props.areaSel) emit('incendio', String(e.features?.[0]?.properties?.id)) })
    puntatore(l)
  }
  m.on('click', 'segn', (e) => emit('segnalazione', Number(e.features?.[0]?.properties?.id)))
  puntatore('segn')
  clicInvasi(m, () => !props.areaSel)
  m.on('click', 'vedette', (e) => {
    const p = e.features![0]!.properties as any
    popupSemplice((e.features![0]!.geometry as any).coordinates, Binoculars, tinte().cielo, 'Vedetta antincendio · simulata', p.nome, p.stato, [['Raggio di avvistamento', `${p.raggio_km} km`]])
  })
  m.on('click', 'fuochi', (e) => {
    const p = e.features![0]!.properties as any
    popupSemplice((e.features![0]!.geometry as any).coordinates, FlameKindling, tinte().viola, 'Fuoco autorizzato · simulato', p.tipo, p.comune,
      [['Fascia oraria', `${p.dalle} - ${p.alle}`], ['Superficie', `${String(p.ettari).replace('.', ',')} ha`], ['Stato', p.stato]])
  })
  m.on('click', 'basi', (e) => {
    if (m.queryRenderedFeatures(e.point, { layers: ['flotta-terra', 'flotta-aerei'] }).length) return
    const p = e.features![0]!.properties as any
    const mezzi = JSON.parse(p.mezzi ?? '[]') as string[]
    popupSemplice((e.features![0]!.geometry as any).coordinates, Building2, (ENTI_BASI as any)[p.ente]?.grad[1] ?? '#888', (ENTI_BASI as any)[p.ente]?.etichetta ?? p.ente, p.nome, p.comune,
      [['Mezzi assegnati', String(mezzi.length)]])
  })
  for (const l of ['flotta-terra', 'flotta-aerei']) {
    m.on('click', l, (e) => {
      const p = e.features![0]!.properties as any
      popupSemplice((e.features![0]!.geometry as any).coordinates, p.categoria === 'aereo' ? Plane : Truck, statoMezzo(p.stato).colore(tema.value), `${FAMIGLIE[p.famiglia as keyof typeof FAMIGLIE]} · simulato`, p.sigla, p.tipo,
        [['Stato', p.stato], ['Base', String(p.base).replace('Servizio territoriale CFVA di ', 'CFVA ')], ...(p.destinazione ? [['Destinazione', p.destinazione] as [string, string]] : [])])
    })
    puntatore(l)
  }
  for (const l of ['vedette', 'fuochi', 'basi']) puntatore(l)
}

// ---------------------------------------------------------------- ciclo di vita

onMounted(() => {
  registraPmtiles()
  mappa = new maplibregl.Map({
    container: contenitore.value!, style: stileMappa(tema.value), bounds: ISOLA as any,
    fitBoundsOptions: { padding: { top: 56, bottom: 48, left: contenitore.value!.clientWidth > 900 ? 470 : 24, right: 56 } },
    attributionControl: { compact: true }, locale: LOCALE_MAPPA, maxPitch: 0, dragRotate: false, minZoom: 6.3,
  })
  mappa.touchZoomRotate.disableRotation()
  mappa.on('style.load', () => aggiungiLivelli(mappa!))
  mappa.on('styleimagemissing', (e: any) => {
    if (/^(mezzo|ombra|base)-/.test(String(e.id))) registraMezzi(mappa!, tema.value)
    else if (String(e.id).startsWith('cop-')) registraSegnaposti(mappa!, segnaposti(), tema.value)
  })
  eventi(mappa)
})
onBeforeUnmount(() => { fermaAloni(); chiudiPopup(); mappa?.remove(); mappa = null })

watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))
const fonte = (id: string) => mappa?.getSource(id) as GeoJSONSource | undefined
watch(() => props.bollettino, (b) => fonte('cfd')?.setData(b?.zone ?? VUOTO))
watch(() => props.incendi, (d) => fonte('incendi')?.setData(d ?? VUOTO))
watch(fcCentri, (d) => fonte('centri')?.setData(d as any))
watch(() => props.fuochi, (d) => fonte('fuochi')?.setData(d ?? VUOTO))
watch(() => props.vedette, (d) => fonte('vedette')?.setData(d ?? VUOTO))
watch(fcRaggi, (d) => fonte('raggi')?.setData(d as any))
watch(() => props.basi, (d) => fonte('basi')?.setData(d ?? VUOTO))
watch(fcFlotta, (d) => fonte('flotta')?.setData(d as any))
watch(fcSegn, (d) => fonte('segn')?.setData(d as any))
watch(fcAree, (d) => { fonte('aree')?.setData(d as any); fonte('sedi')?.setData(fcSedi.value as any); if (mappa) aggiornaStatoAree(mappa) })
watch(() => props.invasi, (d) => impostaInvasi(mappa, d ?? VUOTO, props.livelli.invasi))
watch(() => props.areaHover, () => mappa && aggiornaStatoAree(mappa))
watch(() => props.areaSel, () => {
  if (!mappa) return
  chiudiPopup()
  aggiornaStatoAree(mappa)
  aggiornaMaschera(mappa)
  inquadra()
})
watch(() => props.anni, () => mappa && filtraStorico(mappa))
watch(() => ({ ...props.livelli }), (l) => {
  const m = mappa
  if (!m?.getLayer('cfd-fill')) return
  for (const id of ['cfd-fill', 'cfd-alone', 'cfd-bordo']) m.setLayoutProperty(id, 'visibility', vis(l.rischio))
  for (const id of ['raggi-fill', 'raggi-linea', 'vedette']) m.setLayoutProperty(id, 'visibility', vis(l.vedette))
  m.setLayoutProperty('fuochi', 'visibility', vis(l.fuochi))
  for (const id of ['segn', 'segn-alone']) m.setLayoutProperty(id, 'visibility', vis(l.segnalazioni))
  const filtro = l.incendi && l.spenti ? null : l.incendi ? ['==', ['get', 'stato'], 'attivo'] : l.spenti ? ['==', ['get', 'stato'], 'spento'] : ['==', 1, 0]
  for (const id of ['incendi-fill', 'incendi-linea', 'centri', 'centri-etichetta']) m.setFilter(id, filtro as any)
  for (const id of ['incendi-alone', 'centri-alone']) m.setLayoutProperty(id, 'visibility', vis(l.incendi))
  impostaInvasi(m, props.invasi ?? VUOTO, l.invasi)
  impostaVisOperativo(m, { basi: l.basi, terra: l.terra, aerei: l.aerei })
  filtraStorico(m)
})
</script>

<template>
  <!-- MapLibre impone position: relative al contenitore: la posizione la da' il guscio -->
  <div class="absolute inset-0">
    <div ref="contenitore" class="h-full w-full" role="region" aria-label="Mappa dell'area di competenza" />
  </div>
</template>
