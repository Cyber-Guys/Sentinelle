<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { aggiungiHotspot, aggiungiPinSegnalazioni, geojsonSegnalazioni, animaAloni, apriPopup, ALONE_HOTSPOT, FILTRI_STORICO_INCENDI, aggiungiStoricoIncendi, impostaStoricoIncendi, clicIncendio, registraSegnaposti, segnapostiMancanti, toniMappature, impostaFasceLibere, chiudiPopup, clicHotspot, aggiungiRischio, impostaRischio, geojsonRischio, aggiungiScenario, impostaOraScenario, rimuoviScenario, limitiScenario, ALONE_SCENARIO, aggiungiInvasi, impostaInvasi, clicInvasi, SEGNAPOSTO_INVASO, type GrigliaRischio, type Simulazione } from '~/composables/useMappa'
import PopupMappa from '~/components/PopupMappa.vue'
import PopupSegnalazione from '~/components/PopupSegnalazione.vue'
import { h } from 'vue'
import { Flame, Check, Ban, Droplet, Leaf, Trash2, TriangleAlert, X, ShieldCheck, Loader2, RotateCw, CircleCheck, MapPin, History, Inbox, ArrowLeft, ChevronUp } from '@lucide/vue'

const { chiama } = useApi()
const { tema } = useTema()

const coda = ref<Segnalazione[]>([])
const confermateOggi = ref(0)
const selezionata = ref<number | null>(null)
const errore = ref('')
const caricamento = ref(true)
const inAzione = ref<'conferma' | 'archivia' | null>(null)
const avviso = ref<{ id: number; testo: string; tipo: 'ok' | 'errore' } | null>(null)
let tAvviso: ReturnType<typeof setTimeout> | undefined
// segnalazioni arrivate dopo il primo caricamento: evidenziate per qualche secondo
const conosciute = new Set<number>()
const appena = ref(new Set<number>())
const contenitore = ref<HTMLElement | null>(null)
let mappa: maplibregl.Map | null = null
const mappaPronta = shallowRef<maplibregl.Map | null>(null) // per ControlliMappa
let timer: ReturnType<typeof setInterval> | undefined
const eventi = useEventi()
let fermaEventi: (() => void)[] = []
let fermaAloni = () => {}

const mostraMappature = ref(false)
// risorse idriche (invasi regionali): accese, sono la risorsa dei mezzi aerei
const mostraInvasi = ref(true)
const invasi = shallowRef<any>({ type: 'FeatureCollection', features: [] })
const dataInvasi = computed(() => { const d = invasi.value.features[0]?.properties?.data_dato; if (!d) return ''; const [a, m] = d.split('-'); return new Date(+a, +m - 1).toLocaleDateString('it-IT', { month: 'short', year: 'numeric' }) })
watch([invasi, mostraInvasi], () => impostaInvasi(mappa, invasi.value, mostraInvasi.value))
const mostraHotspot = ref(true)
const livelliAperti = ref(false)
const mostraStorico = ref(false)
// Rischio di oggi: spento di default, la griglia si scarica alla prima accensione
const mostraRischio = ref(false)
const griglia = shallowRef<GrigliaRischio | null>(null)
const carRischio = ref(false)
const errRischio = ref(false)
async function caricaRischio() {
  if (griglia.value || carRischio.value) return
  carRischio.value = true; errRischio.value = false
  try { griglia.value = await chiama<GrigliaRischio>('/rischio/griglia') } catch { errRischio.value = true }
  carRischio.value = false
  impostaRischio(mappa, geojsonRischio(griglia.value), mostraRischio.value)
}
watch(mostraRischio, (v) => { if (v) caricaRischio(); impostaRischio(mappa, geojsonRischio(griglia.value), v) })

/*
  Scenario di propagazione: avvio da popup hotspot, scheda segnalazione, clic destro / pressione lunga.
  Il pannello sostituisce la scheda (desktop) o il contenuto del foglio (telefono).
*/
const scenario = ref<{ lat: number; lon: number; titolo: string } | null>(null)
const oreScenario = ref(6)
const cursore = ref(6)
const datiScenario = shallowRef<Simulazione | null>(null)
const carScenario = ref(false)
const errScenario = ref('')
let richiesta = 0
const coordinate = (lat: number, lon: number) => `${lat.toFixed(3)}, ${lon.toFixed(3)}`
function avviaScenario(lat: number, lon: number, titolo = '') {
  chiudiPopup()
  livelliAperti.value = false
  selezionata.value = null
  scenario.value = { lat, lon, titolo: titolo ? nomeComune(titolo) : coordinate(lat, lon) }
  datiScenario.value = null
  rimuoviScenario(mappa)
  if (mobile.value && foglio.value === 'chiuso') foglio.value = 'meta'
  calcolaScenario(true)
}
async function calcolaScenario(adatta = false) {
  const s = scenario.value
  if (!s) return
  const n = ++richiesta
  carScenario.value = true; errScenario.value = ''
  try {
    const d = await chiama<Simulazione>('/simulazione', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ lat: s.lat, lon: s.lon, ore: oreScenario.value }) })
    if (n !== richiesta || !scenario.value) return
    datiScenario.value = d
    cursore.value = d.ore
    if (mappa) aggiungiScenario(mappa, coloriMappa(tema.value), d, d.ore)
    const b = limitiScenario(d)
    // primo calcolo: inquadra l'area finale; dopo un cambio di orizzonte solo se l'area esce dalla vista
    const fuori = () => { const v = mappa!.getBounds(); return !v.contains(b![0]) || !v.contains(b![1]) }
    if (b && mappa && (adatta || fuori())) mappa.fitBounds(b, { padding: paddingScenario(), maxZoom: 13, duration: 900 })
  } catch (e) {
    if (n === richiesta) errScenario.value = messaggioErrore(e, 'calcolare lo scenario')
  }
  if (n === richiesta) carScenario.value = false
}
// spazio libero per l'area, in aggiunta al padding della mappa (paddingMappa: coda a sinistra / header e foglio chiuso):
// a destra il pannello (desktop), in basso il foglio a meta' (telefono)
const paddingScenario = () => (mobile.value
  ? { top: 24, bottom: ALTEZZE.value.meta - ALTEZZE.value.chiuso + 24, left: 24, right: 72 }
  : { top: 40, bottom: 70, left: 40, right: 74 + 416 + 40 })
function chiudiScenario() {
  richiesta++
  scenario.value = null
  datiScenario.value = null
  carScenario.value = false; errScenario.value = ''
  rimuoviScenario(mappa)
}
watch(oreScenario, () => calcolaScenario())
watch(cursore, (o) => impostaOraScenario(mappa, coloriMappa(tema.value), o))
const vaiAcqua = (lon: number, lat: number) => mappa?.flyTo({ center: [lon, lat], zoom: Math.max(mappa.getZoom(), 12), padding: paddingScenario() })
const mostraIncendi = ref(true)
const filtroIncendi = ref('2025')
const filtroStorico = ref<'entrambe' | 'confermata' | 'archiviata'>('entrambe')
const FILTRI_STORICO = [
  { id: 'entrambe', etichetta: 'Entrambe' }, { id: 'confermata', etichetta: 'Confermate' }, { id: 'archiviata', etichetta: 'Falsi allarmi' },
] as const
// segnalazioni gia' valutate: si ricaricano all'accensione del livello e dopo ogni valutazione (non nel polling)
const storico = ref<Segnalazione[]>([])
const nLivelli = computed(() => Number(mostraRischio.value) + Number(mostraHotspot.value) + Number(mostraMappature.value) + Number(mostraInvasi.value) + Number(mostraStorico.value) + Number(mostraIncendi.value))
const TIPI_MAPPATURA = [
  { codice: 'punto_acqua', etichetta: 'Punto d\'acqua', breve: 'Acqua', colore: 'cielo', icona: Droplet },
  { codice: 'sterpaglie', etichetta: 'Sterpaglie secche', breve: 'Sterpaglie', colore: 'ambra', icona: Leaf },
  { codice: 'rifiuti_strada', etichetta: 'Rifiuti a bordo strada', breve: 'Rifiuti', colore: 'viola', icona: Trash2 },
] as const
// segnaposto a icona per tipo (+ generico per codici sconosciuti), colori del tema corrente
const segnapostiMappature = () => {
  const c = toniMappature(tema.value)
  return [...TIPI_MAPPATURA.map((t) => ({ id: `mappa-${t.codice}`, icona: t.icona, colore: c[t.colore] })), { id: 'mappa-altro', icona: MapPin, colore: c.grigio }]
}
// ordine di disegno: piu' a sud sopra (pin ancorati in basso, come Waze)
const conOrdine = (g: any) => ({ ...g, features: g.features.map((f: any) => ({ ...f, properties: { ...f.properties, ordine: -f.geometry.coordinates[1] } })) })
const nMappature = ref(0)
let timerMappature: ReturnType<typeof setInterval> | undefined
let firmaMappature = ''
// setData solo se qualcosa e' cambiato, per non ridisegnare i cluster a vuoto.
function caricaMappature() {
  chiama<any>('/mappature').then((g) => {
    const firma = `${g.features.length}:${g.features.map((f: any) => f.properties?.completata_il).sort().at(-1) ?? ''}`
    if (firma === firmaMappature) return
    firmaMappature = firma
    datiMappature = g = conOrdine(g)
    nMappature.value = g.features.length
    ;(mappa?.getSource('mappature') as maplibregl.GeoJSONSource | undefined)?.setData(g)
  }).catch(() => {})
}
let datiMappature: any = { type: 'FeatureCollection', features: [] }
let datiHotspot: any = { type: 'FeatureCollection', features: [] }

const scheda = computed(() => coda.value.find((s) => s.id === selezionata.value) ?? storico.value.find((s) => s.id === selezionata.value) ?? null)
const sola = computed(() => !!scheda.value && scheda.value.stato !== 'nuova') // scheda in sola lettura

const ora = (iso: string) => new Date(iso).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
const fa = (iso: string) => {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'adesso'
  if (min < 60) return `${min} min fa`
  if (min < 1440) return `${Math.round(min / 60)} h fa`
  return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
}

function geojsonCoda() {
  return {
    type: 'FeatureCollection' as const,
    features: coda.value.map((s) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [s.lon, s.lat] },
      properties: { id: s.id, priorita: s.priorita, selezionata: s.id === selezionata.value ? 1 : 0 },
    })),
  }
}

function aggiornaMappa() {
  (mappa?.getSource('coda') as maplibregl.GeoJSONSource | undefined)?.setData(geojsonCoda());
  (mappa?.getSource('storico-segn') as maplibregl.GeoJSONSource | undefined)?.setData(geojsonSegnalazioni(storico.value, selezionata.value))
}

async function caricaStorico() {
  try { storico.value = await chiama<Segnalazione[]>('/segnalazioni?stato=valutate'); aggiornaMappa() } catch {}
}
const filtroStoricoMappa = () => (filtroStorico.value === 'entrambe' ? null : ['==', ['get', 'stato'], filtroStorico.value]) as any
function livelloStorico() {
  if (!mappa?.getLayer('storico-segn')) return
  mappa.setLayoutProperty('storico-segn', 'visibility', mostraStorico.value ? 'visible' : 'none')
  mappa.setFilter('storico-segn', filtroStoricoMappa())
}
watch(mostraStorico, (v) => { livelloStorico(); if (v) caricaStorico() })
watch(filtroStorico, livelloStorico)
// scheda attiva del box Segnalazioni: resta finche' l'operatore non la cambia
const schedaBox = ref<'nuova' | 'confermata' | 'archiviata'>('nuova')
const SCHEDE_BOX = [{ id: 'nuova', etichetta: 'In coda' }, { id: 'confermata', etichetta: 'Confermate' }, { id: 'archiviata', etichetta: 'Falsi allarmi' }] as const
const valutate = computed(() => storico.value.filter((s) => s.stato === schedaBox.value).sort((a, b) => (b.valutata_il ?? '').localeCompare(a.valutata_il ?? '')))
const nBox = computed(() => ({ nuova: coda.value.length, confermata: nStorico.value.confermata, archiviata: nStorico.value.archiviata }))
// nelle schede valutate il livello Storico si accende col filtro coerente; tornando In coda torna com'era
let prima: { mostra: boolean; filtro: typeof filtroStorico.value } | null = null
watch(schedaBox, (v) => {
  if (v === 'nuova') {
    if (prima) { mostraStorico.value = prima.mostra; filtroStorico.value = prima.filtro; prima = null }
    return
  }
  prima ??= { mostra: mostraStorico.value, filtro: filtroStorico.value }
  filtroStorico.value = v
  mostraStorico.value = true
  caricaStorico()
})
let timerValutate: ReturnType<typeof setInterval> | undefined
const nStorico = computed(() => ({ confermata: storico.value.filter((s) => s.stato === 'confermata').length, archiviata: storico.value.filter((s) => s.stato === 'archiviata').length }))

function mostraAvviso(testo: string, tipo: 'ok' | 'errore' = 'ok') {
  avviso.value = { id: Date.now(), testo, tipo }
  clearTimeout(tAvviso); tAvviso = setTimeout(() => (avviso.value = null), 3000)
}

function caricaHotspot() {
  chiama<any>('/hotspot').then((g) => { datiHotspot = g; (mappa?.getSource('hotspot') as maplibregl.GeoJSONSource | undefined)?.setData(g) }).catch(() => {})
}

async function aggiorna() {
  try {
    const l = await chiama<Segnalazione[]>('/segnalazioni?stato=nuova')
    if (!caricamento.value) {
      const nuove = l.filter((s) => !conosciute.has(s.id)).map((s) => s.id)
      if (nuove.length) {
        appena.value = new Set([...appena.value, ...nuove])
        setTimeout(() => { const a = new Set(appena.value); nuove.forEach((id) => a.delete(id)); appena.value = a }, 4000)
      }
    }
    l.forEach((s) => conosciute.add(s.id))
    coda.value = l
    caricamento.value = false
    if (selezionata.value && !scheda.value) selezionata.value = null
    errore.value = ''
    aggiornaMappa()
    const oggi = new Date().toDateString()
    chiama<Segnalazione[]>('/segnalazioni?stato=confermata')
      .then((l) => (confermateOggi.value = l.filter((s) => s.valutata_il && new Date(s.valutata_il).toDateString() === oggi).length))
      .catch(() => {})
  } catch { errore.value = 'Connessione persa' }
}

watch(selezionata, (id) => { aggiornaMappa(); if (id && scenario.value) chiudiScenario() })
const LIVELLI_MAPPATURE = ['mappature-cluster', 'mappature-conteggio', 'mappature']
watch(mostraMappature, (v) => { for (const l of LIVELLI_MAPPATURE) mappa?.setLayoutProperty(l, 'visibility', v ? 'visible' : 'none') })
const visibilitaHotspot = () => { for (const l of ['hotspot-alone', 'hotspot']) mappa?.setLayoutProperty(l, 'visibility', mostraHotspot.value ? 'visible' : 'none') }
watch(mostraHotspot, visibilitaHotspot)
// durante lo scenario lo storico (stessi colori caldi) si nasconde: l'area simulata resta l'unico fuoco sulla carta
watch([mostraIncendi, filtroIncendi, () => !!scenario.value], () => impostaStoricoIncendi(mappa, filtroIncendi.value, mostraIncendi.value && !scenario.value))
watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))

// sorgenti e layer: richiamata a ogni stile caricato (anche dopo il cambio tema)
function aggiungiLivelli() {
  const m = mappa
  if (!m || m.getSource('coda')) return
  const c = coloriMappa(tema.value)
  const prio: any = ['step', ['get', 'priorita'], c.macchia, 30, c.ambra, 60, c.brace]
  aggiungiStoricoIncendi(m, c, filtroIncendi.value, mostraIncendi.value && !scenario.value) // sotto a tutto il resto
  aggiungiRischio(m, c, geojsonRischio(griglia.value), mostraRischio.value, 'storico-riempimento') // sotto lo storico
  aggiungiHotspot(m, c, datiHotspot)
  visibilitaHotspot()
  // mappature: raggruppate fino a zoom 11 (cerchio di vetro con numero), poi segnaposto a icona
  const tm = toniMappature(tema.value)
  const visMappature = mostraMappature.value ? 'visible' : 'none'
  m.addSource('mappature', { type: 'geojson', data: datiMappature, cluster: true, clusterMaxZoom: 11, clusterRadius: 40, clusterMinPoints: 3 })
  m.addLayer({ id: 'mappature-cluster', type: 'circle', source: 'mappature', filter: ['has', 'point_count'], layout: { visibility: visMappature }, paint: {
    'circle-color': tm.vetro, 'circle-stroke-color': tm.anello, 'circle-stroke-width': 1.5,
    'circle-radius': ['interpolate', ['linear'], ['get', 'point_count'], 2, 12, 10, 14, 40, 17] as any,
  } })
  m.addLayer({ id: 'mappature-conteggio', type: 'symbol', source: 'mappature', filter: ['has', 'point_count'], layout: {
    visibility: visMappature, 'text-field': ['get', 'point_count_abbreviated'], 'text-font': ['Noto Sans Medium'], 'text-size': 11.5,
    'text-allow-overlap': true, 'text-ignore-placement': true,
  }, paint: { 'text-color': tm.testo2 } })
  registraSegnaposti(m, segnapostiMappature(), tema.value) // prima del layer: niente immagini mancanti
  m.addLayer({ id: 'mappature', type: 'symbol', source: 'mappature', filter: ['!', ['has', 'point_count']], layout: {
    visibility: visMappature,
    'icon-image': ['match', ['get', 'codice'], ...TIPI_MAPPATURA.flatMap((t) => [t.codice, `mappa-${t.codice}`]), 'mappa-altro'] as any,
    'icon-anchor': 'bottom',
    'icon-size': ['interpolate', ['linear'], ['zoom'], 6, 0.7, 11, 1] as any,
    'icon-allow-overlap': true, 'icon-ignore-placement': true,
    'symbol-sort-key': ['get', 'ordine'],
  } })
  aggiungiInvasi(m, tema.value, invasi.value, mostraInvasi.value)
  // storico delle segnalazioni valutate: sotto la coda attiva, pin fermi (confermata piena, falso allarme ad anello)
  aggiungiPinSegnalazioni(m, 'storico-segn', c, geojsonSegnalazioni(storico.value, selezionata.value), { nuova: prio, confermata: prio })
  livelloStorico()
  m.addSource('coda', { type: 'geojson', data: geojsonCoda() })
  // valori statici = alone fisso con reduced-motion; animaAloni li fa pulsare
  m.addLayer({ id: 'coda-alone', type: 'circle', source: 'coda', paint: { 'circle-radius': 16, 'circle-color': prio, 'circle-opacity': 0.22, 'circle-blur': 0.3 } })
  // selezionata: anello del colore della priorita' che si allarga, piu' rapido
  m.addLayer({ id: 'coda-selezione', type: 'circle', source: 'coda', filter: ['==', ['get', 'selezionata'], 1], paint: { 'circle-radius': 22, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': prio, 'circle-stroke-width': 2, 'circle-stroke-opacity': 0.6 } })
  m.addLayer({ id: 'coda', type: 'circle', source: 'coda', paint: {
    'circle-radius': ['case', ['==', ['get', 'selezionata'], 1], 12, 8],
    'circle-color': prio,
    'circle-stroke-color': ['case', ['==', ['get', 'selezionata'], 1], c.testo, c.bordo],
    'circle-stroke-width': ['case', ['==', ['get', 'selezionata'], 1], 3, 2],
  } })
  // scenario attivo: sopra a tutto, ripristinato anche dopo il cambio tema
  if (datiScenario.value) aggiungiScenario(m, c, datiScenario.value, cursore.value)
}

onMounted(() => {
  registraPmtiles()
  mappa = new maplibregl.Map({ container: contenitore.value!, style: stileMappa(tema.value), center: [9.0, 40.1], zoom: 7.4, attributionControl: false, locale: LOCALE_MAPPA })
  limitaMappa(mappa)
  paddingMappa()
  mappaPronta.value = mappa
  mappa.on('style.load', aggiungiLivelli)
  segnapostiMancanti(mappa, () => [...segnapostiMappature(), SEGNAPOSTO_INVASO(tema.value)], () => tema.value)
  chiama<any>('/invasi').then((g) => (invasi.value = g)).catch(() => {})
  // Fuori da 'load': lo strato si crea su style.load e prende datiMappature da qui.
  caricaMappature()
  // Gestori registrati subito, non su 'load' (puo' non arrivare se una risorsa della mappa fallisce).
  {
    const m = mappa
    m.on('click', 'mappature', (ev) => {
      const p = ev.features?.[0]?.properties
      if (!p || m.queryRenderedFeatures(ev.point, { layers: ['hotspot', 'invasi'].filter((l) => m.getLayer(l)) }).length) return
      const t = TIPI_MAPPATURA.find((x) => x.codice === p.codice)
      const tinta = t ? [toniMappature('scuro')[t.colore], toniMappature('chiaro')[t.colore]] : ['var(--testo-2)', 'var(--testo-2)']
      apriPopup(m, ev.lngLat, PopupMappa, {
        icona: t?.icona ?? MapPin, tinta, etichetta: `Mappatura · ${t?.breve ?? 'cittadino'}`, titolo: p.titolo,
        sottotitolo: [p.utente, p.comune ? nomeComune(String(p.comune)) : ''].filter(Boolean).join(' · '),
      }, () => h('p', { class: 'cifre mt-2.5 border-t border-bordo pt-2 text-[.75rem] text-testo-3' }, `Completata · ${ora(p.completata_il)}`))
    })
    // cluster: zoom fino a dove il gruppo si separa
    m.on('click', 'mappature-cluster', async (ev) => {
      const f = ev.features?.[0]
      if (!f) return
      const z = await (m.getSource('mappature') as maplibregl.GeoJSONSource).getClusterExpansionZoom(f.properties!.cluster_id)
      // centro reale della mappa: il box segnalazioni in alto a sinistra e' basso, non serve compensarlo
      m.easeTo({ center: (f.geometry as any).coordinates, zoom: Math.min(z + 0.5, m.getMaxZoom()), padding: { left: 0, top: 80, right: 0, bottom: 60 } })
    })
    clicIncendio(m, ['coda', 'storico-segn', 'mappature', 'mappature-cluster', 'hotspot', 'invasi'])
    clicInvasi(m)
    clicHotspot(m, ['coda', 'storico-segn'], () => false, avviaScenario)
    // clic destro (desktop) o pressione lunga (touch) su un punto qualunque: scenario da li'
    let ultimaPressione = 0
    m.on('contextmenu', (ev) => {
      ev.preventDefault()
      if (Date.now() - ultimaPressione < 1000) return
      avviaScenario(ev.lngLat.lat, ev.lngLat.lng)
    })
    let pressione: ReturnType<typeof setTimeout> | undefined
    let inizio: { x: number; y: number } | null = null
    const annulla = () => { clearTimeout(pressione); inizio = null }
    m.on('touchstart', (ev) => {
      annulla()
      if (ev.originalEvent.touches.length !== 1) return
      inizio = { x: ev.point.x, y: ev.point.y }
      const ll = ev.lngLat
      pressione = setTimeout(() => { ultimaPressione = Date.now(); inizio = null; navigator.vibrate?.(15); avviaScenario(ll.lat, ll.lng) }, 600)
    })
    m.on('touchmove', (ev) => { if (inizio && Math.hypot(ev.point.x - inizio.x, ev.point.y - inizio.y) > 10) annulla() })
    m.on('touchend', annulla)
    m.on('touchcancel', annulla)
    m.on('movestart', (ev: any) => { if (ev.originalEvent) annulla() })
    m.on('click', 'coda', (ev) => { selezionata.value = ev.features?.[0]?.properties?.id ?? null })
    m.on('click', 'storico-segn', (ev) => {
      // la coda attiva sta sopra: se il clic e' anche su un pin della coda vince quello
      if (m.queryRenderedFeatures(ev.point, { layers: ['coda'] }).length) return
      const s = storico.value.find((x) => x.id === ev.features?.[0]?.properties?.id)
      if (s) apriPopup(m, [s.lon, s.lat], PopupSegnalazione, { s, azione: () => (selezionata.value = s.id) })
    })
    for (const l of ['storico-segn', 'mappature', 'mappature-cluster']) {
      m.on('mouseenter', l, () => (m.getCanvas().style.cursor = 'pointer'))
      m.on('mouseleave', l, () => (m.getCanvas().style.cursor = ''))
    }
    m.on('mouseenter', 'coda', () => (m.getCanvas().style.cursor = 'pointer'))
    m.on('mouseleave', 'coda', () => (m.getCanvas().style.cursor = ''))
    caricaHotspot()
    // pin pulsanti: segnalazioni nuove (onda), selezionata (anello piu' rapido), hotspot (respiro lento)
    fermaAloni = animaAloni(m, [
      { layer: 'coda-alone', periodo: 2600, da: 9, a: 27, opacita: 0.45 },
      { layer: 'coda-selezione', periodo: 1600, da: 13, a: 34, opacita: 0.9, tratto: true },
      ALONE_HOTSPOT,
      ALONE_SCENARIO,
    ])
  }
  aggiorna()
  caricaStorico() // serve anche alla scheda in sola lettura
  // aggiornamenti dagli eventi SSE; il polling ogni 30 s e' solo una rete di sicurezza
  const valutate = () => { if (schedaBox.value !== 'nuova') caricaStorico() }
  timer = setInterval(aggiorna, 30000)
  timerValutate = setInterval(valutate, 30000)
  timerMappature = setInterval(caricaMappature, 30000)
  fermaEventi = [
    eventi.on('segnalazione_nuova', aggiorna),
    eventi.on('segnalazione_valutata', () => { aggiorna(); valutate() }),
    eventi.on('mappatura_nuova', caricaMappature),
    eventi.on('hotspot_aggiornati', caricaHotspot),
  ]
})

onBeforeUnmount(() => { fermaTelefono(); fermaEventi.forEach((f) => f()); clearInterval(timer); clearInterval(timerValutate); clearInterval(timerMappature); clearTimeout(tAvviso); fermaAloni(); mappa?.remove() })

function seleziona(s: Segnalazione) {
  selezionata.value = s.id
  if (mobile.value) return // sul telefono ci pensa il watch su `selezionata` (anche per i pin)
  mappa?.flyTo({ center: [s.lon, s.lat], zoom: Math.max(mappa.getZoom(), 11), padding: { left: 400, right: 510, top: 80, bottom: 60 } })
}

async function azione(tipo: 'conferma' | 'archivia') {
  if (!scheda.value || inAzione.value) return
  const id = scheda.value.id
  inAzione.value = tipo
  try {
    await chiama(`/segnalazioni/${id}/${tipo}`, { method: 'POST' })
    selezionata.value = null
    caricaStorico()
    mostraAvviso(tipo === 'conferma' ? `Segnalazione #${id} confermata` : `Segnalazione #${id} archiviata come falso allarme`)
    await aggiorna()
  } catch (e) { mostraAvviso(messaggioErrore(e, tipo === 'conferma' ? 'confermare la segnalazione' : 'archiviare la segnalazione'), 'errore') }
  inAzione.value = null
}

const nCoda = useConteggio(() => coda.value.length)
const nConfermate = useConteggio(() => confermateOggi.value)
const nMappe = useConteggio(() => nMappature.value)
/*
  Telefono (< 768 px): mappa a tutto schermo, header a una fila, colonna destra come l'app,
  foglio Segnalazioni in basso a tre altezze (chiuso / meta' / alto) trascinabile dalla maniglia.
*/
const mq = window.matchMedia('(max-width: 767px)')
const mobile = ref(mq.matches)
type StatoFoglio = 'chiuso' | 'meta' | 'alto'
const foglio = ref<StatoFoglio>('chiuso')
const vh = ref(window.innerHeight)
const sicuro = ref(0) // safe-area in basso
const colonna = ref<HTMLElement | null>(null)
const bordiColonna = ref({ alto: 70, basso: 266 })
const ALTEZZE = computed(() => ({ chiuso: 64 + sicuro.value, meta: Math.round(vh.value * 0.5), alto: Math.round(vh.value * 0.85) }))
const trascinata = ref<number | null>(null) // altezza visibile durante il trascinamento
const hFoglio = computed(() => trascinata.value ?? ALTEZZE.value[foglio.value])
const hPiede = computed(() => 56 + Math.max(12, sicuro.value))
// piede con le azioni: sempre visibile nel dettaglio, tranne a foglio chiuso
const conPiede = computed(() => mobile.value && !!scheda.value && hFoglio.value > ALTEZZE.value.chiuso + 80)
// la colonna destra sparisce quando il foglio la coprirebbe
const colonnaCoperta = computed(() => mobile.value && vh.value - hFoglio.value < bordiColonna.value.basso + 14)
// la parte del foglio sotto lo schermo si compensa con padding: l'elenco scorre fino all'ultima riga
const padScroll = computed(() => ALTEZZE.value.alto - ALTEZZE.value[foglio.value] + (conPiede.value ? hPiede.value : 0) + 12)
const maxLivelli = computed(() => `${vh.value - bordiColonna.value.alto - ALTEZZE.value.chiuso - 14}px`)
const prioMax = computed(() => coda.value.reduce((m, s) => Math.max(m, s.priorita), 0))

function misura() {
  vh.value = window.innerHeight
  const sonda = document.createElement('div')
  sonda.style.cssText = 'position:fixed;bottom:0;height:env(safe-area-inset-bottom);visibility:hidden'
  document.body.appendChild(sonda); sicuro.value = sonda.offsetHeight; sonda.remove()
  const r = colonna.value?.getBoundingClientRect()
  if (r) bordiColonna.value = { alto: Math.round(r.top), basso: Math.round(r.top + r.height) }
}
function paddingMappa() {
  // desktop: la colonna della coda copre la sinistra, il centro utile si sposta a destra
  mappa?.setPadding(mobile.value ? { left: 0, top: 56, right: 0, bottom: ALTEZZE.value.chiuso } : { left: 400, top: 80, right: 0, bottom: 0 })
  aggiornaFasce()
}
const cambioMq = () => { mobile.value = mq.matches }
mq.addEventListener('change', cambioMq)
window.addEventListener('resize', misura)
onMounted(() => nextTick(misura))
const fermaTelefono = () => { mq.removeEventListener('change', cambioMq); window.removeEventListener('resize', misura) }
watch(mobile, async () => { paddingMappa(); await nextTick(); misura() })
// popup della mappa: la fascia libera in basso segue il foglio
function aggiornaFasce() {
  if (mappa) impostaFasceLibere(mappa, mobile.value ? { alto: 72, basso: ALTEZZE.value[foglio.value] + 12, destra: 70, sinistra: 12 } : { alto: 72, basso: 156 })
}
watch([mobile, foglio, ALTEZZE], aggiornaFasce)
// il foglio che sale coprirebbe i popup: si chiudono
watch(foglio, (f) => { if (mobile.value && f !== 'chiuso') chiudiPopup() })
// selezione (dall'elenco o dal pin): foglio almeno a meta', pin al centro dello spazio libero sopra il foglio
watch(selezionata, async (id) => {
  if (!mobile.value || !id) return
  if (foglio.value === 'chiuso') foglio.value = 'meta'
  livelliAperti.value = false
  chiudiPopup()
  await nextTick()
  const s = scheda.value
  if (!s || !mappa) return
  mappa.flyTo({ center: [s.lon, s.lat], zoom: Math.max(mappa.getZoom(), 11), padding: { top: 72, bottom: ALTEZZE.value[foglio.value] + 24, left: 24, right: 72 } })
})
// pannello Livelli aperto: il foglio scende a striscia per lasciargli spazio
watch(livelliAperti, (v) => { if (v && mobile.value) foglio.value = 'chiuso' })

let presa: { y: number; h: number; mosso: boolean; v: number; ly: number; lt: number } | null = null
function giu(e: PointerEvent) {
  if ((e.target as HTMLElement).closest('a, input, label, button:not([data-maniglia])')) return
  presa = { y: e.clientY, h: hFoglio.value, mosso: false, v: 0, ly: e.clientY, lt: e.timeStamp }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}
function muovi(e: PointerEvent) {
  if (!presa) return
  const dy = presa.y - e.clientY
  if (!presa.mosso && Math.abs(dy) < 6) return
  presa.mosso = true
  const dt = e.timeStamp - presa.lt
  if (dt > 0) presa.v = (presa.ly - e.clientY) / dt
  presa.ly = e.clientY; presa.lt = e.timeStamp
  const a = ALTEZZE.value
  trascinata.value = Math.min(a.alto, Math.max(a.chiuso, presa.h + dy))
}
function su(e: PointerEvent) {
  const p = presa
  presa = null
  if (!p) return
  if (!p.mosso) { if (e.type === 'pointerup') alternaFoglio(); return }
  // aggancio allo stato piu' vicino alla posizione proiettata (tiene conto della velocita' del gesto)
  const meta = (trascinata.value ?? p.h) + p.v * 180
  const a = ALTEZZE.value
  foglio.value = (['chiuso', 'meta', 'alto'] as const).reduce((x, k) => (Math.abs(a[k] - meta) < Math.abs(a[x] - meta) ? k : x), 'chiuso' as StatoFoglio)
  trascinata.value = null
}
function alternaFoglio() { foglio.value = foglio.value === 'chiuso' ? 'meta' : 'chiuso' }

const contatori = computed(() => [
  { etichetta: 'in coda', valore: nCoda.value, colore: coda.value.length ? 'var(--brace)' : 'var(--testo)' },
  { etichetta: 'confermate oggi', valore: nConfermate.value, colore: 'var(--testo)' },
  { etichetta: 'mappature', valore: nMappe.value, colore: 'var(--testo)' },
])
const contatoriBrevi = computed(() => [
  { ...contatori.value[0]!, icona: Inbox },
  { ...contatori.value[1]!, icona: CircleCheck },
  { ...contatori.value[2]!, icona: MapPin },
])
</script>

<template>
  <main class="relative h-dvh overflow-hidden" :class="mobile && 'cruscotto-telefono'">
    <div class="cruscotto-mappa absolute inset-0"><div ref="contenitore" class="h-full w-full" /></div>

    <!-- barra superiore: marchio, stato, contatori -->
    <header v-if="!mobile" class="pointer-events-none absolute inset-x-4 top-4 z-20 flex items-center gap-3">
      <NuxtLink to="/" class="pillola pointer-events-auto flex h-12 items-center gap-2.5 pr-4 pl-2 transition-colors hover:bg-vetro-forte">
        <span class="flex size-8 items-center justify-center rounded-full bg-gradient-to-b from-[#f2581d] to-[#d33515]"><Flame class="size-4 text-white" aria-hidden="true" /></span>
        <span class="leading-tight">
          <span class="block text-[.9rem] font-semibold">Sentinelle</span>
          <span class="block text-[.68rem] text-testo-3">Sala operativa</span>
        </span>
      </NuxtLink>

      <div class="pillola pointer-events-auto flex h-12 items-center divide-x divide-bordo px-1">
        <div v-for="c in contatori" :key="c.etichetta" class="flex items-baseline gap-2 px-3.5">
          <span class="cifre text-lg font-semibold leading-none" :style="{ color: c.colore }">{{ c.valore }}</span>
          <span class="text-[.72rem] leading-tight whitespace-nowrap text-testo-2">{{ c.etichetta }}</span>
        </div>
        <!-- stato del collegamento: ultimo segmento della stessa pillola -->
        <span v-if="!errore" class="flex items-center gap-2.5 px-3.5 text-[.72rem] whitespace-nowrap text-testo-2" role="status">
          <span class="punto-vivo" :class="eventi.stato.value === 'riconnessione' && 'punto-ambra'" aria-hidden="true" />
          {{ eventi.stato.value === 'connesso' ? 'In diretta' : 'Riconnessione…' }}
        </span>
        <button v-else type="button" class="flex h-full items-center gap-2.5 rounded-r-full px-3.5 text-[.72rem] whitespace-nowrap text-testo-2 transition-colors hover:bg-vetro-forte" role="status" aria-label="Connessione persa: riprova adesso" @click="aggiorna">
          <span class="punto-vivo punto-ambra" aria-hidden="true" />
          <span><span class="font-semibold text-testo">Connessione persa</span> · riprovo da solo</span>
          <RotateCw class="size-3.5 text-testo-3" aria-hidden="true" />
        </button>
      </div>

      <InterruttoreTema class="pointer-events-auto ml-auto" />
    </header>

    <!-- telefono: una sola fila, marchio solo icona, contatori brevi, stato, tema -->
    <header v-else class="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center gap-2 px-3 pt-[max(.75rem,env(safe-area-inset-top))]">
      <NuxtLink to="/" class="pillola pointer-events-auto flex size-11 shrink-0 items-center justify-center transition-colors hover:bg-vetro-forte" aria-label="Sentinelle, sala operativa: torna all'inizio">
        <span class="flex size-8 items-center justify-center rounded-full bg-gradient-to-b from-[#f2581d] to-[#d33515]"><Flame class="size-4 text-white" aria-hidden="true" /></span>
      </NuxtLink>
      <div class="pillola pointer-events-auto flex h-11 min-w-0 items-center pl-3">
        <span v-for="c in contatoriBrevi" :key="c.etichetta" class="flex items-center gap-1 pr-3">
          <component :is="c.icona" class="size-3.5 shrink-0 text-testo-3" aria-hidden="true" />
          <span class="cifre text-[.95rem] font-semibold leading-none" :style="{ color: c.colore }">{{ c.valore }}</span>
          <span class="sr-only">{{ c.etichetta }}</span>
        </span>
        <span v-if="!errore" class="flex h-11 w-9 items-center justify-center border-l border-bordo" role="status">
          <span class="punto-vivo" :class="eventi.stato.value === 'riconnessione' && 'punto-ambra'" aria-hidden="true" />
          <span class="sr-only">{{ eventi.stato.value === 'connesso' ? 'In diretta' : 'Riconnessione…' }}</span>
        </span>
        <button v-else type="button" class="flex h-11 w-11 items-center justify-center rounded-r-full border-l border-bordo transition-colors hover:bg-vetro-forte" role="status" aria-label="Connessione persa: riprova adesso" @click="aggiorna">
          <span class="punto-vivo punto-ambra" aria-hidden="true" />
        </button>
      </div>
      <span class="flex-1" />
      <InterruttoreTema compatto class="pointer-events-auto" />
    </header>

    <!-- colonna della coda: cresce col contenuto, si ferma sopra la barra in basso, poi scorre -->
    <aside v-if="!mobile" class="vetro absolute top-[4.75rem] left-4 z-10 flex max-h-[calc(100%-4.75rem-4rem)] w-[23rem] flex-col !bg-[var(--vetro-mappa)] shadow-[var(--ombra-pillola)]" aria-label="Segnalazioni">
      <div class="shrink-0 space-y-2.5 border-b border-bordo p-3 pt-3.5">
        <h1 class="px-2 text-[.92rem] font-semibold">Segnalazioni</h1>
        <SchedeStato v-model="schedaBox" :schede="SCHEDE_BOX" :conteggi="nBox" />
      </div>
      <ElencoSegnalazioni :scheda="schedaBox" :coda="coda" :valutate="valutate" :caricamento="caricamento" :errore="errore" :selezionata="selezionata" :appena="appena" @seleziona="seleziona" @riprova="aggiorna" />
    </aside>

    <!-- scheda della segnalazione selezionata -->
    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 translate-x-3" leave-active-class="transition duration-150" leave-to-class="opacity-0 translate-x-3">
      <!-- a sinistra della colonna destra (16 + 44 + 14); col pannello Livelli aperto scorre a sinistra del pannello -->
      <section v-if="scheda && !mobile && !scenario" class="sospeso absolute top-[4.75rem] z-10 flex max-h-[calc(100%-4.75rem-1rem)] w-[26rem] flex-col overflow-hidden transition-[right] duration-200 ease-out" :style="{ right: livelliAperti ? 'calc(68px + min(17.5rem, 100vw - 5.5rem) + 14px)' : '74px' }" aria-labelledby="titolo-scheda">
        <header class="flex shrink-0 items-start justify-between gap-3 border-b border-bordo px-5 py-3.5">
          <div class="min-w-0">
            <p class="flex items-center gap-2 text-[.72rem] text-testo-3">
              <span v-if="!sola" class="rounded-full bg-cielo/12 px-2 py-px font-medium text-cielo">Nuova</span>
              <span v-else class="rounded-full px-2 py-px font-medium" :style="{ color: STATI[scheda.stato].colore, background: `color-mix(in srgb, ${STATI[scheda.stato].colore} 14%, transparent)` }">{{ STATI[scheda.stato].etichetta }}</span>
              <span class="cifre">#{{ scheda.id }} · {{ ora(scheda.creata_il) }} · {{ fa(scheda.creata_il) }}</span>
            </p>
            <h2 id="titolo-scheda" class="mt-1 flex items-center gap-1.5 text-base font-semibold">
              <Flame v-if="scheda.tipo === 'fuoco'" class="size-4 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-4 text-ambra" aria-hidden="true" />
              {{ scheda.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<span v-if="scheda.comune" class="font-normal text-testo-2"> · {{ nomeComune(scheda.comune) }}</span>
            </h2>
          </div>
          <button type="button" aria-label="Chiudi la scheda" class="secondario tocco flex size-8 shrink-0 items-center justify-center" @click="selezionata = null"><X class="size-4" /></button>
        </header>
        <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <CorpoScheda :s="scheda" @simula="avviaScenario(scheda.lat, scheda.lon, scheda.comune ?? '')" />
        </div>
        <!-- valutata: esito al posto delle azioni -->
        <footer v-if="sola" class="flex shrink-0 items-center gap-3 border-t border-bordo px-5 py-3.5">
          <span class="flex h-10 items-center gap-1.5 rounded-full px-4 text-sm font-semibold" :style="{ color: STATI[scheda.stato].colore, background: `color-mix(in srgb, ${STATI[scheda.stato].colore} 14%, transparent)` }">
            <Check v-if="scheda.stato === 'confermata'" class="size-4" aria-hidden="true" /><Ban v-else class="size-4" aria-hidden="true" />{{ STATI[scheda.stato].etichetta }}
          </span>
          <span class="cifre text-[.76rem] leading-tight text-testo-2">Valutata<br>{{ ora(scheda.valutata_il ?? scheda.creata_il) }}</span>
        </footer>
        <footer v-else class="grid shrink-0 grid-cols-[1fr_auto] gap-2 border-t border-bordo px-5 py-3.5">
          <button class="primario flex h-10 items-center justify-center gap-1.5 text-sm" :disabled="!!inAzione" @click="azione('conferma')">
            <Loader2 v-if="inAzione === 'conferma'" class="size-4 animate-spin" aria-hidden="true" /><Check v-else class="size-4" aria-hidden="true" /> Conferma
          </button>
          <button class="secondario flex h-10 items-center justify-center gap-1.5 px-4 text-sm text-testo-2" :disabled="!!inAzione" aria-label="Archivia come falso allarme" @click="azione('archivia')">
            <Loader2 v-if="inAzione === 'archivia'" class="size-4 animate-spin" aria-hidden="true" /><Ban v-else class="size-4" aria-hidden="true" /> Falso allarme
          </button>
        </footer>
      </section>
    </Transition>

    <!-- scenario: stesso posto e larghezza della scheda -->
    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 translate-x-3" leave-active-class="transition duration-150" leave-to-class="opacity-0 translate-x-3">
      <section v-if="scenario && !mobile" class="sospeso absolute top-[4.75rem] z-10 flex max-h-[calc(100%-4.75rem-1rem)] w-[26rem] flex-col overflow-hidden transition-[right] duration-200 ease-out" :style="{ right: livelliAperti ? 'calc(68px + min(17.5rem, 100vw - 5.5rem) + 14px)' : '74px' }" aria-labelledby="titolo-scenario">
        <PannelloScenario v-model:ore="oreScenario" v-model:cursore="cursore" :titolo="scenario.titolo" :dati="datiScenario" :caricamento="carScenario" :errore="errScenario" @chiudi="chiudiScenario" @riprova="calcolaScenario()" @vai="vaiAcqua" />
      </section>
    </Transition>

    <!-- colonna destra come nell'app: Livelli, zoom, "i" (passo 14 px dal flex) -->
    <!-- telefono: stessa colonna dell'app (sotto l'header, passo 14 px); sparisce quando il foglio la coprirebbe -->
    <div ref="colonna" class="absolute z-20 flex w-11 flex-col items-center gap-[14px]" :class="mobile ? ['top-[calc(max(.75rem,env(safe-area-inset-top))+58px)] right-3 transition-opacity duration-200', colonnaCoperta && 'pointer-events-none opacity-0'] : 'top-[4.75rem] right-4'" :inert="colonnaCoperta || undefined">
    <PulsanteLivelli v-model:aperto="livelliAperti" v-model="filtroIncendi" v-model:acceso="mostraIncendi" :filtri="FILTRI_STORICO_INCENDI" :badge="String(nLivelli)" :descrizione="`${nLivelli} attivi`" :max-altezza="mobile ? maxLivelli : undefined" class="relative">
      <div class="space-y-1">
        <LivelloRischio v-model="mostraRischio" :griglia="griglia" :caricamento="carRischio" :errore="errRischio" />
        <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
          <input v-model="mostraHotspot" type="checkbox" role="switch" class="sr-only" />
          <span class="size-2.5 shrink-0 rounded-full bg-brace ring-2 ring-fondo" aria-hidden="true" />
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block text-[.86rem] font-semibold">Hotspot satellitari</span>
            <span class="block text-[.72rem] text-testo-2">VIIRS, ultime 24 h</span>
          </span>
          <span class="interruttore" :class="mostraHotspot && 'acceso'" aria-hidden="true" />
        </label>
        <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
          <input v-model="mostraMappature" type="checkbox" role="switch" class="sr-only" />
          <MapPin class="size-4 shrink-0 text-macchia" aria-hidden="true" />
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block text-[.86rem] font-semibold">Mappature dei cittadini</span>
            <span class="cifre block text-[.72rem] text-testo-2">{{ nMappature }} completate dalle missioni</span>
          </span>
          <span class="interruttore" :class="mostraMappature && 'acceso'" aria-hidden="true" />
        </label>
        <div v-if="mostraMappature" class="px-3 pt-1 pb-1 text-[.74rem]">
          <p v-if="!nMappature" class="text-testo-2">Ancora nessuna mappatura: arrivano dalle missioni dei cittadini.</p>
          <ul v-else class="flex flex-wrap gap-x-3 gap-y-1">
            <li v-for="t in TIPI_MAPPATURA" :key="t.codice" class="flex items-center gap-1.5 whitespace-nowrap text-testo-2">
              <span class="grid size-[18px] place-items-center rounded-full shadow-sm" :style="{ background: toniMappature(tema).vetro, boxShadow: `inset 0 0 0 1.5px ${toniMappature(tema)[t.colore]}`, color: toniMappature(tema)[t.colore] }" aria-hidden="true"><component :is="t.icona" class="size-[10px]" :stroke-width="2.6" /></span>{{ t.etichetta }}
            </li>
          </ul>
        </div>
        <LivelloInvasi v-model="mostraInvasi" :n="invasi.features.length" :data="dataInvasi" />
        <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
          <input v-model="mostraStorico" type="checkbox" role="switch" class="sr-only" />
          <History class="size-4 shrink-0 text-testo-2" aria-hidden="true" />
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block text-[.86rem] font-semibold">Storico segnalazioni</span>
            <span class="cifre block text-[.72rem] text-testo-2">{{ nStorico.confermata }} confermate · {{ nStorico.archiviata }} falsi allarmi</span>
          </span>
          <span class="interruttore" :class="mostraStorico && 'acceso'" aria-hidden="true" />
        </label>
        <div v-if="mostraStorico" class="px-3 pt-1 pb-1">
          <div class="flex rounded-full bg-vetro p-0.5 ring-1 ring-bordo" role="radiogroup" aria-label="Filtro dello storico">
            <label v-for="f in FILTRI_STORICO" :key="f.id" class="flex flex-1 cursor-pointer items-center justify-center rounded-full text-[.74rem] font-medium whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="[mobile ? 'h-11' : 'h-8', filtroStorico === f.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo']">
              <input v-model="filtroStorico" type="radio" name="filtro-storico-segn" :value="f.id" class="sr-only" />{{ f.etichetta }}
            </label>
          </div>
          <ul class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[.74rem] text-testo-2">
            <li class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media ring-[1.5px] ring-testo" aria-hidden="true" />Confermata, fissa</li>
            <li class="flex items-center gap-1.5"><span class="size-2 rounded-full ring-[1.5px] ring-testo-3" aria-hidden="true" />Falso allarme</li>
          </ul>
        </div>
        <!-- telefono: la legenda sta qui, non in basso (li' c'e' il foglio); incendi, hotspot, storico e mappature hanno la loro accanto al livello -->
        <section v-if="mobile" class="mt-2 border-t border-bordo px-3 pt-3 pb-1 text-[.76rem] text-testo-2" aria-labelledby="titolo-legenda">
          <h3 id="titolo-legenda" class="etichetta mb-2">Legenda</h3>
          <ul class="space-y-1.5">
            <li class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span class="w-full text-testo-3">Priorità delle segnalazioni</span>
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-alta" aria-hidden="true" />Alta <span class="cifre text-testo-3">60+</span></span>
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media" aria-hidden="true" />Media <span class="cifre text-testo-3">30-59</span></span>
              <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-bassa" aria-hidden="true" />Bassa <span class="cifre text-testo-3">0-29</span></span>
            </li>
          </ul>
        </section>
      </div>
    </PulsanteLivelli>
    <ControlliMappa :mappa="mappaPronta" />
    </div>

    <!-- legenda (solo informativa): priorita' delle segnalazioni, hotspot se il livello e' acceso -->
    <div v-if="!mobile" class="pillola pointer-events-none absolute bottom-4 left-4 z-10 flex h-9 items-center gap-3 px-3 text-[.74rem] whitespace-nowrap" aria-label="Legenda della mappa">
      <span class="etichetta">Priorità</span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-alta" />Alta <span class="cifre text-testo-3">60+</span></span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media" />Media <span class="cifre text-testo-3">30-59</span></span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-bassa" />Bassa <span class="cifre text-testo-3">0-29</span></span>
      <span v-if="mostraStorico" class="flex items-center gap-3 border-l border-bordo pl-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media ring-[1.5px] ring-testo" />Confermata</span><span class="flex items-center gap-1.5"><span class="size-2 rounded-full ring-[1.5px] ring-testo-3" />Falso allarme</span></span>
      <span v-if="mostraIncendi && !scenario" class="flex items-center gap-1.5 border-l border-bordo pl-3"><span class="legenda-storico h-1.5 w-8 rounded-full" />Incendi storici</span>
      <span v-if="mostraHotspot" class="flex items-center gap-1.5 border-l border-bordo pl-3"><span class="size-2 rounded-full bg-brace ring-2 ring-fondo" />Hotspot</span>
      <span v-if="mostraRischio" class="flex items-center gap-1.5 border-l border-bordo pl-3"><span class="legenda-rischio h-1.5 w-8 rounded-full" />Rischio di oggi</span>
      <span v-if="!scenario" class="border-l border-bordo pl-3 text-testo-3">Clic destro: simula scenario</span>
    </div>

    <!-- telefono: foglio Segnalazioni a tre altezze; si sposta con transform, l'altezza resta quella massima -->
    <section
      v-if="mobile"
      class="sospeso foglio-telefono fixed inset-x-0 bottom-0 z-30 flex flex-col !rounded-b-none"
      :class="trascinata !== null && 'trascinando'"
      :style="{ height: `${ALTEZZE.alto}px`, transform: `translateY(${ALTEZZE.alto - hFoglio}px)` }"
      aria-label="Segnalazioni"
    >
      <div class="shrink-0 cursor-grab touch-none select-none" @pointerdown="giu" @pointermove="muovi" @pointerup="su" @pointercancel="su">
        <button data-maniglia type="button" class="tocco flex h-4 w-full items-end justify-center" :aria-label="foglio === 'chiuso' ? 'Apri il foglio delle segnalazioni' : 'Riduci il foglio delle segnalazioni'" :aria-expanded="foglio !== 'chiuso'">
          <span class="h-1 w-9 rounded-full bg-bordo-luce" aria-hidden="true" />
        </button>
        <!-- elenco: riepilogo; dettaglio: indietro + titolo; scenario: intestazione nel pannello -->
        <div v-if="scenario" />
        <div v-else-if="!scheda" class="flex h-12 items-center gap-3 px-4">
          <template v-if="errore">
            <span class="punto-vivo punto-ambra shrink-0" aria-hidden="true" />
            <p class="min-w-0 flex-1 truncate text-[.92rem]"><span class="font-semibold">Connessione persa</span> <span class="text-testo-2">· riprovo da solo</span></p>
          </template>
          <p v-else-if="caricamento" class="flex-1 text-[.92rem] text-testo-2">Caricamento della coda…</p>
          <p v-else-if="coda.length" class="cifre min-w-0 flex-1 truncate text-[.92rem]">
            <span class="font-semibold text-brace">{{ coda.length }}</span> in coda <span class="text-testo-3">·</span> priorità max <span class="font-semibold" :style="{ color: varPriorita(prioMax) }">{{ prioMax }}</span>
          </p>
          <p v-else class="flex min-w-0 flex-1 items-center gap-2 text-[.92rem] font-semibold"><ShieldCheck class="size-4 shrink-0 text-macchia" aria-hidden="true" />Tutto tranquillo</p>
          <ChevronUp class="size-4 shrink-0 text-testo-3 transition-transform duration-200" :class="foglio !== 'chiuso' && 'rotate-180'" aria-hidden="true" />
        </div>
        <div v-else class="flex h-12 items-center gap-2 pr-4 pl-2">
          <button type="button" class="flex size-11 shrink-0 items-center justify-center rounded-full text-testo-2 transition-colors hover:bg-vetro-forte" aria-label="Torna all'elenco" @click="selezionata = null"><ArrowLeft class="size-5" aria-hidden="true" /></button>
          <div class="min-w-0 flex-1 leading-tight">
            <p class="flex items-center gap-1.5 text-[.72rem] text-testo-3">
              <span v-if="!sola" class="rounded-full bg-cielo/12 px-2 py-px font-medium text-cielo">Nuova</span>
              <span v-else class="rounded-full px-2 py-px font-medium" :style="{ color: STATI[scheda.stato].colore, background: `color-mix(in srgb, ${STATI[scheda.stato].colore} 14%, transparent)` }">{{ STATI[scheda.stato].etichetta }}</span>
              <span class="cifre truncate">#{{ scheda.id }} · {{ fa(scheda.creata_il) }}</span>
            </p>
            <h2 class="mt-0.5 flex min-w-0 items-center gap-1.5 text-[.95rem] font-semibold">
              <Flame v-if="scheda.tipo === 'fuoco'" class="size-4 shrink-0 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-4 shrink-0 text-ambra" aria-hidden="true" />
              <span class="truncate">{{ scheda.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<span v-if="scheda.comune" class="font-normal text-testo-2"> · {{ nomeComune(scheda.comune) }}</span></span>
            </h2>
          </div>
        </div>
      </div>
      <PannelloScenario v-if="scenario" v-model:ore="oreScenario" v-model:cursore="cursore" telefono :pad-fondo="padScroll" :titolo="scenario.titolo" :dati="datiScenario" :caricamento="carScenario" :errore="errScenario" @chiudi="chiudiScenario" @riprova="calcolaScenario()" @vai="vaiAcqua" />
      <div v-else-if="!scheda" class="shrink-0 border-b border-bordo px-3 pb-3">
        <SchedeStato v-model="schedaBox" :schede="SCHEDE_BOX" :conteggi="nBox" grande />
      </div>
      <div v-if="!scenario" class="min-h-0 flex-1 overflow-y-auto overscroll-contain" :class="scheda && 'border-t border-bordo'" :style="{ paddingBottom: `${padScroll}px` }">
        <ElencoSegnalazioni v-if="!scheda" :scheda="schedaBox" :coda="coda" :valutate="valutate" :caricamento="caricamento" :errore="errore" :selezionata="selezionata" :appena="appena" @seleziona="seleziona" @riprova="aggiorna" />
        <div v-else class="space-y-4 px-4 pt-4"><CorpoScheda :s="scheda" @simula="avviaScenario(scheda.lat, scheda.lon, scheda.comune ?? '')" /></div>
      </div>
    </section>
    <!-- piede del dettaglio: azioni (in coda) o esito (valutata), sempre visibile sopra il foglio -->
    <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-150 ease-in" leave-to-class="opacity-0 translate-y-2">
      <footer v-if="conPiede && scheda" class="fixed inset-x-0 bottom-0 z-40 border-t border-bordo bg-fondo px-4 pt-3 pb-[max(.75rem,env(safe-area-inset-bottom))]">
        <div v-if="sola" class="flex h-11 items-center gap-3">
          <span class="flex h-11 items-center gap-1.5 rounded-full px-4 text-sm font-semibold" :style="{ color: STATI[scheda.stato].colore, background: `color-mix(in srgb, ${STATI[scheda.stato].colore} 14%, transparent)` }">
            <Check v-if="scheda.stato === 'confermata'" class="size-4" aria-hidden="true" /><Ban v-else class="size-4" aria-hidden="true" />{{ STATI[scheda.stato].etichetta }}
          </span>
          <span class="cifre text-[.76rem] leading-tight text-testo-2">Valutata<br>{{ ora(scheda.valutata_il ?? scheda.creata_il) }}</span>
        </div>
        <div v-else class="grid grid-cols-[1fr_auto] gap-2">
          <button class="primario flex h-11 items-center justify-center gap-1.5 text-sm" :disabled="!!inAzione" @click="azione('conferma')">
            <Loader2 v-if="inAzione === 'conferma'" class="size-4 animate-spin" aria-hidden="true" /><Check v-else class="size-4" aria-hidden="true" /> Conferma
          </button>
          <button class="secondario flex h-11 items-center justify-center gap-1.5 px-4 text-sm text-testo-2" :disabled="!!inAzione" aria-label="Archivia come falso allarme" @click="azione('archivia')">
            <Loader2 v-if="inAzione === 'archivia'" class="size-4 animate-spin" aria-hidden="true" /><Ban v-else class="size-4" aria-hidden="true" /> Falso allarme
          </button>
        </div>
      </footer>
    </Transition>

    <!-- esito delle azioni dell'operatore -->
    <Transition enter-active-class="transition duration-250 ease-out" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0 translate-y-1">
      <div v-if="avviso" :key="avviso.id" class="pointer-events-none absolute bottom-16 left-1/2 -translate-x-1/2" :class="mobile ? 'z-50 w-max max-w-[calc(100vw-2rem)]' : 'z-30'" :style="mobile ? { bottom: `${hFoglio + 12}px` } : undefined" role="status">
        <span class="sospeso flex items-center gap-2 !rounded-full py-2 pr-4 pl-3 text-sm font-medium">
          <CircleCheck v-if="avviso.tipo === 'ok'" class="size-4 text-macchia" aria-hidden="true" />
          <TriangleAlert v-else class="size-4 text-ambra" aria-hidden="true" />
          {{ avviso.testo }}
        </span>
      </div>
    </Transition>
  </main>
</template>

<style>
/* nuove segnalazioni: entrano scivolando e restano evidenziate per qualche secondo */
.coda-enter-active { transition: opacity .3s ease-out, transform .35s cubic-bezier(.22, 1, .36, 1); }
.coda-leave-active { transition: opacity .2s ease-in; position: absolute; left: .75rem; right: .75rem; }
.coda-enter-from { opacity: 0; transform: translateX(-12px); }
.coda-leave-to { opacity: 0; }
.coda-move { transition: transform .3s cubic-bezier(.22, 1, .36, 1); }
@keyframes arrivo { from { box-shadow: 0 0 0 1px var(--brace); } to { box-shadow: 0 0 0 1px transparent, 0 0 0 0 transparent; } }
.appena-arrivata { animation: arrivo 3.6s ease-out forwards; }
/* foglio del telefono: segue il dito durante il trascinamento, poi aggancia con easing in uscita */
.foglio-telefono { transition: transform .32s cubic-bezier(.22, 1, .36, 1); will-change: transform; }
.foglio-telefono.trascinando { transition: none; }
/* popup della mappa sul telefono: non arrivano sotto la colonna destra (12 + 44 + 14 a destra, 12 a sinistra) */
.cruscotto-telefono .popup-sentinelle .maplibregl-popup-content { width: min(280px, calc(100vw - 94px)); }
@media (prefers-reduced-motion: reduce) { .foglio-telefono { transition: none; } }
</style>
