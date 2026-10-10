<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { aggiungiHotspot, aggiungiPinSegnalazioni, geojsonSegnalazioni, animaAloni, apriPopup, ALONE_HOTSPOT, FILTRI_STORICO_INCENDI, aggiungiStoricoIncendi, impostaStoricoIncendi, clicIncendio, registraSegnaposti, segnapostiMancanti, toniMappature } from '~/composables/useMappa'
import PopupMappa from '~/components/PopupMappa.vue'
import PopupSegnalazione from '~/components/PopupSegnalazione.vue'
import { h } from 'vue'
import { Flame, Check, Ban, Droplet, Leaf, Trash2, TriangleAlert, X, ShieldCheck, Loader2, RotateCw, CircleCheck, ExternalLink, MapPin, History } from '@lucide/vue'

const { chiama, urlFoto } = useApi()
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
let fermaAloni = () => {}

const mostraMappature = ref(false)
const mostraHotspot = ref(true)
const livelliAperti = ref(false)
const mostraStorico = ref(false)
const mostraIncendi = ref(true)
const filtroIncendi = ref('2025')
const filtroStorico = ref<'entrambe' | 'confermata' | 'archiviata'>('entrambe')
const FILTRI_STORICO = [
  { id: 'entrambe', etichetta: 'Entrambe' }, { id: 'confermata', etichetta: 'Confermate' }, { id: 'archiviata', etichetta: 'Falsi allarmi' },
] as const
// segnalazioni gia' valutate: si ricaricano all'accensione del livello e dopo ogni valutazione (non nel polling)
const storico = ref<Segnalazione[]>([])
const nLivelli = computed(() => Number(mostraHotspot.value) + Number(mostraMappature.value) + Number(mostraStorico.value) + Number(mostraIncendi.value))
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
const VUOTO_BOX = { nuova: '', confermata: 'Nessuna segnalazione confermata', archiviata: 'Nessun falso allarme archiviato' }
const valutate = computed(() => storico.value.filter((s) => s.stato === schedaBox.value).sort((a, b) => (b.valutata_il ?? '').localeCompare(a.valutata_il ?? '')))
const nBox = computed(() => ({ nuova: coda.value.length, confermata: nStorico.value.confermata, archiviata: nStorico.value.archiviata }))
const faValutata = (iso: string | null | undefined) => {
  if (!iso) return ''
  const d = new Date(iso), min = Math.round((Date.now() - d.getTime()) / 60000)
  if (min < 60) return fa(iso)
  const ore = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  const giorni = Math.round((new Date().setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86400000)
  if (giorni === 0) return fa(iso)
  if (giorni === 1) return `ieri ${ore}`
  return `${d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })} ${ore}`
}
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

watch(selezionata, aggiornaMappa)
const LIVELLI_MAPPATURE = ['mappature-cluster', 'mappature-conteggio', 'mappature']
watch(mostraMappature, (v) => { for (const l of LIVELLI_MAPPATURE) mappa?.setLayoutProperty(l, 'visibility', v ? 'visible' : 'none') })
const visibilitaHotspot = () => { for (const l of ['hotspot-alone', 'hotspot']) mappa?.setLayoutProperty(l, 'visibility', mostraHotspot.value ? 'visible' : 'none') }
watch(mostraHotspot, visibilitaHotspot)
watch([mostraIncendi, filtroIncendi], () => impostaStoricoIncendi(mappa, filtroIncendi.value, mostraIncendi.value))
watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))

// sorgenti e layer: richiamata a ogni stile caricato (anche dopo il cambio tema)
function aggiungiLivelli() {
  const m = mappa
  if (!m || m.getSource('coda')) return
  const c = coloriMappa(tema.value)
  const prio: any = ['step', ['get', 'priorita'], c.macchia, 30, c.ambra, 60, c.brace]
  aggiungiStoricoIncendi(m, c, filtroIncendi.value, mostraIncendi.value) // sotto a tutto il resto
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
}

onMounted(() => {
  registraPmtiles()
  mappa = new maplibregl.Map({ container: contenitore.value!, style: stileMappa(tema.value), center: [9.0, 40.1], zoom: 7.4, attributionControl: false, locale: LOCALE_MAPPA })
  limitaMappa(mappa)
  // la colonna della coda copre la sinistra: il centro utile della mappa si sposta a destra
  mappa.setPadding({ left: 400, top: 80, right: 0, bottom: 0 })
  mappaPronta.value = mappa
  mappa.on('style.load', aggiungiLivelli)
  segnapostiMancanti(mappa, segnapostiMappature, () => tema.value)
  // Fuori da 'load': lo strato si crea su style.load e prende datiMappature da qui.
  caricaMappature()
  mappa.on('load', () => {
    const m = mappa!
    m.on('click', 'mappature', (ev) => {
      const p = ev.features?.[0]?.properties
      if (!p) return
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
    clicIncendio(m, ['coda', 'storico-segn', 'mappature', 'mappature-cluster', 'hotspot'])
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
    chiama<any>('/hotspot').then((g) => { datiHotspot = g; (m.getSource('hotspot') as maplibregl.GeoJSONSource | undefined)?.setData(g) }).catch(() => {})
    // pin pulsanti: segnalazioni nuove (onda), selezionata (anello piu' rapido), hotspot (respiro lento)
    fermaAloni = animaAloni(m, [
      { layer: 'coda-alone', periodo: 2600, da: 9, a: 27, opacita: 0.45 },
      { layer: 'coda-selezione', periodo: 1600, da: 13, a: 34, opacita: 0.9, tratto: true },
      ALONE_HOTSPOT,
    ])
  })
  aggiorna()
  caricaStorico() // serve anche alla scheda in sola lettura
  timer = setInterval(aggiorna, 3000)
  timerValutate = setInterval(() => { if (schedaBox.value !== 'nuova') caricaStorico() }, 10000)
  // le missioni dei cittadini arrivano in qualunque momento: aggiornamento leggero ogni 5 s
  timerMappature = setInterval(caricaMappature, 5000)
})

onBeforeUnmount(() => { clearInterval(timer); clearInterval(timerValutate); clearInterval(timerMappature); clearTimeout(tAvviso); fermaAloni(); mappa?.remove() })

function seleziona(s: Segnalazione) {
  selezionata.value = s.id
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
const contatori = computed(() => [
  { etichetta: 'in coda', valore: nCoda.value, colore: coda.value.length ? 'var(--brace)' : 'var(--testo)' },
  { etichetta: 'confermate oggi', valore: nConfermate.value, colore: 'var(--testo)' },
  { etichetta: 'mappature', valore: nMappe.value, colore: 'var(--testo)' },
])
</script>

<template>
  <main class="relative h-dvh overflow-hidden">
    <div class="cruscotto-mappa absolute inset-0"><div ref="contenitore" class="h-full w-full" /></div>

    <!-- barra superiore: marchio, stato, contatori -->
    <header class="pointer-events-none absolute inset-x-4 top-4 z-20 flex items-center gap-3">
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
          <span class="punto-vivo" aria-hidden="true" />
          In diretta · ogni 3 s
        </span>
        <button v-else type="button" class="flex h-full items-center gap-2.5 rounded-r-full px-3.5 text-[.72rem] whitespace-nowrap text-testo-2 transition-colors hover:bg-vetro-forte" role="status" aria-label="Connessione persa: riprova adesso" @click="aggiorna">
          <span class="punto-vivo punto-ambra" aria-hidden="true" />
          <span><span class="font-semibold text-testo">Connessione persa</span> · riprovo da solo</span>
          <RotateCw class="size-3.5 text-testo-3" aria-hidden="true" />
        </button>
      </div>

      <InterruttoreTema class="pointer-events-auto ml-auto" />
    </header>

    <!-- colonna della coda: cresce col contenuto, si ferma sopra la barra in basso, poi scorre -->
    <aside class="vetro absolute top-[4.75rem] left-4 z-10 flex max-h-[calc(100%-4.75rem-4rem)] w-[23rem] flex-col !bg-[var(--vetro-mappa)] shadow-[var(--ombra-pillola)]" aria-label="Segnalazioni">
      <div class="shrink-0 space-y-2.5 border-b border-bordo p-3 pt-3.5">
        <h1 class="px-2 text-[.92rem] font-semibold">Segnalazioni</h1>
        <div class="flex rounded-full bg-vetro p-0.5 ring-1 ring-bordo" role="radiogroup" aria-label="Stato delle segnalazioni">
          <label v-for="f in SCHEDE_BOX" :key="f.id" class="flex h-8 flex-1 cursor-pointer items-center justify-center gap-1.5 rounded-full text-[.74rem] font-medium whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="schedaBox === f.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo'">
            <input v-model="schedaBox" type="radio" name="scheda-segnalazioni" :value="f.id" class="sr-only" />{{ f.etichetta }}<span class="cifre text-testo-3">{{ nBox[f.id] }}</span>
          </label>
        </div>
      </div>
      <div v-if="schedaBox !== 'nuova'" class="contents">
        <div v-if="!valutate.length" class="px-5 py-3.5 text-[.8rem] text-testo-2">{{ VUOTO_BOX[schedaBox] }}</div>
        <ul v-else class="relative min-h-0 space-y-px overflow-y-auto p-3">
          <li v-for="s in valutate" :key="s.id">
            <button class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors" :class="s.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60'" :aria-current="s.id === selezionata ? 'true' : undefined" @click="seleziona(s)">
              <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: varPriorita(s.priorita) }" aria-hidden="true" />
              <span class="cifre w-8 shrink-0 text-right text-[1.05rem] font-semibold" :style="{ color: varPriorita(s.priorita) }" :aria-label="`Priorità ${s.priorita}`">{{ s.priorita }}</span>
              <span class="min-w-0 flex-1 leading-tight">
                <span class="flex items-center gap-1.5 text-[.86rem] font-medium">
                  <Flame v-if="s.tipo === 'fuoco'" class="size-3.5 shrink-0 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-3.5 shrink-0 text-ambra" aria-hidden="true" />
                  <span class="truncate">{{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
                </span>
                <span class="cifre mt-0.5 block text-[.72rem] text-testo-3">#{{ s.id }} · {{ faValutata(s.valutata_il) }}</span>
              </span>
              <span class="shrink-0 rounded-full px-2 py-px text-[.7rem] font-medium" :style="{ color: STATI[s.stato].colore, background: `color-mix(in srgb, ${STATI[s.stato].colore} 14%, transparent)` }">{{ STATI[s.stato].etichetta }}</span>
            </button>
          </li>
        </ul>
      </div>
      <div v-else-if="caricamento && errore" class="p-3"><StatoErrore compatto messaggio="Non riusciamo a raggiungere il servizio. La coda si aggiorna da sola appena torna la connessione." @riprova="aggiorna" /></div>
      <ul v-else-if="caricamento" class="space-y-px p-3" aria-busy="true" aria-label="Caricamento della coda">
        <li v-for="k in 4" :key="k" class="flex items-center gap-3 px-2 py-2.5">
          <span class="scheletro h-6 w-8 shrink-0" />
          <span class="flex-1 space-y-1.5"><span class="scheletro block h-3 w-28" /><span class="scheletro block h-2.5 w-40" /></span>
        </li>
      </ul>
      <div v-else-if="!coda.length" class="flex items-center gap-3 px-5 py-3.5">
        <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-macchia/12 text-macchia"><ShieldCheck class="size-4" aria-hidden="true" /></span>
        <div class="leading-tight">
          <p class="text-[.86rem] font-semibold">Tutto tranquillo</p>
          <p class="mt-0.5 text-[.76rem] text-testo-2">Le nuove segnalazioni compaiono qui, ordinate per priorità.</p>
        </div>
      </div>
      <TransitionGroup v-else tag="ul" name="coda" class="relative min-h-0 space-y-px overflow-y-auto p-3">
        <li v-for="s in coda" :key="s.id">
          <button
            class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors"
            :class="[s.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60', appena.has(s.id) && 'appena-arrivata']"
            :aria-current="s.id === selezionata ? 'true' : undefined"
            @click="seleziona(s)"
          >
            <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: varPriorita(s.priorita) }" aria-hidden="true" />
            <span class="cifre w-8 shrink-0 text-right text-[1.05rem] font-semibold" :style="{ color: varPriorita(s.priorita) }" :aria-label="`Priorità ${s.priorita}`">{{ s.priorita }}</span>
            <span class="min-w-0 flex-1 leading-tight">
              <span class="flex items-center gap-1.5 text-[.86rem] font-medium">
                <Flame v-if="s.tipo === 'fuoco'" class="size-3.5 shrink-0 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-3.5 shrink-0 text-ambra" aria-hidden="true" />
                <span class="truncate">{{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
              </span>
              <span class="cifre mt-0.5 block text-[.72rem] text-testo-3">#{{ s.id }} · {{ fa(s.creata_il) }}</span>
            </span>
            <span class="shrink-0 text-[.7rem] font-medium" :style="{ color: varPriorita(s.priorita) }">{{ etichettaPriorita(s.priorita) }}</span>
          </button>
        </li>
      </TransitionGroup>
    </aside>

    <!-- scheda della segnalazione selezionata -->
    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 translate-x-3" leave-active-class="transition duration-150" leave-to-class="opacity-0 translate-x-3">
      <!-- a sinistra della colonna destra (16 + 44 + 14); col pannello Livelli aperto scorre a sinistra del pannello -->
      <section v-if="scheda" class="sospeso absolute top-[4.75rem] z-10 flex max-h-[calc(100%-4.75rem-1rem)] w-[26rem] flex-col overflow-hidden transition-[right] duration-200 ease-out" :style="{ right: livelliAperti ? 'calc(68px + min(17.5rem, 100vw - 5.5rem) + 14px)' : '74px' }" aria-labelledby="titolo-scheda">
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
          <div class="grid gap-2" :class="scheda.foto_url ? 'grid-cols-[7.5rem_1fr]' : 'grid-cols-1'">
            <a v-if="scheda.foto_url" :href="urlFoto(scheda.foto_url)!" target="_blank" rel="noopener" class="group relative block h-[5.5rem] overflow-hidden rounded-m border border-bordo bg-vetro-forte" aria-label="Apri la foto a dimensione piena">
              <img :key="scheda.id" :src="urlFoto(scheda.foto_url)!" alt="Foto allegata alla segnalazione" class="size-full object-cover" />
              <ExternalLink class="absolute right-1.5 bottom-1.5 size-3.5 text-white opacity-0 drop-shadow transition-opacity group-hover:opacity-100" aria-hidden="true" />
            </a>
            <dl class="grid content-start gap-y-1.5 text-[.76rem]">
              <div class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Posizione</dt><dd class="cifre text-testo-2">{{ scheda.lat.toFixed(5) }}, {{ scheda.lon.toFixed(5) }}</dd></div>
              <div v-if="scheda.comune" class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Comune</dt><dd class="text-testo-2">{{ nomeComune(scheda.comune) }}</dd></div>
              <div v-if="!scheda.foto_url" class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Foto</dt><dd class="text-testo-3">nessuna</dd></div>
            </dl>
          </div>
          <ScomposizionePriorita :priorita="scheda.priorita" :fattori="scheda.fattori" :motivazioni="scheda.motivazioni" />
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

    <!-- colonna destra come nell'app: Livelli, zoom, "i" (passo 14 px dal flex) -->
    <div class="absolute top-[4.75rem] right-4 z-20 flex w-11 flex-col items-center gap-[14px]">
    <PulsanteLivelli v-model:aperto="livelliAperti" v-model="filtroIncendi" v-model:acceso="mostraIncendi" :filtri="FILTRI_STORICO_INCENDI" :badge="String(nLivelli)" :descrizione="`${nLivelli} attivi`" class="relative">
      <div class="space-y-1">
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
            <label v-for="f in FILTRI_STORICO" :key="f.id" class="flex h-8 flex-1 cursor-pointer items-center justify-center rounded-full text-[.74rem] font-medium whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="filtroStorico === f.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo'">
              <input v-model="filtroStorico" type="radio" name="filtro-storico-segn" :value="f.id" class="sr-only" />{{ f.etichetta }}
            </label>
          </div>
          <ul class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[.74rem] text-testo-2">
            <li class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media ring-[1.5px] ring-testo" aria-hidden="true" />Confermata, fissa</li>
            <li class="flex items-center gap-1.5"><span class="size-2 rounded-full ring-[1.5px] ring-testo-3" aria-hidden="true" />Falso allarme</li>
          </ul>
        </div>
      </div>
    </PulsanteLivelli>
    <ControlliMappa :mappa="mappaPronta" />
    </div>

    <!-- legenda (solo informativa): priorita' delle segnalazioni, hotspot se il livello e' acceso -->
    <div class="pillola pointer-events-none absolute bottom-4 left-4 z-10 flex h-9 items-center gap-3 px-3 text-[.74rem] whitespace-nowrap" aria-label="Legenda della mappa">
      <span class="etichetta">Priorità</span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-alta" />Alta <span class="cifre text-testo-3">60+</span></span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media" />Media <span class="cifre text-testo-3">30-59</span></span>
      <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-bassa" />Bassa <span class="cifre text-testo-3">0-29</span></span>
      <span v-if="mostraStorico" class="flex items-center gap-3 border-l border-bordo pl-3"><span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-media ring-[1.5px] ring-testo" />Confermata</span><span class="flex items-center gap-1.5"><span class="size-2 rounded-full ring-[1.5px] ring-testo-3" />Falso allarme</span></span>
      <span v-if="mostraIncendi" class="flex items-center gap-1.5 border-l border-bordo pl-3"><span class="legenda-storico h-1.5 w-8 rounded-full" />Incendi storici</span>
      <span v-if="mostraHotspot" class="flex items-center gap-1.5 border-l border-bordo pl-3"><span class="size-2 rounded-full bg-brace ring-2 ring-fondo" />Hotspot</span>
    </div>

    <!-- esito delle azioni dell'operatore -->
    <Transition enter-active-class="transition duration-250 ease-out" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0 translate-y-1">
      <div v-if="avviso" :key="avviso.id" class="pointer-events-none absolute bottom-16 left-1/2 z-30 -translate-x-1/2" role="status">
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
/* interruttore on/off delle sezioni del pannello Livelli */
.interruttore { position: relative; width: 34px; height: 20px; flex-shrink: 0; border-radius: 999px; background: var(--vetro-forte); box-shadow: inset 0 0 0 1px var(--bordo-luce); transition: background .18s; }
.interruttore::after { content: ''; position: absolute; top: 3px; left: 3px; width: 14px; height: 14px; border-radius: 999px; background: var(--testo-3); transition: transform .18s cubic-bezier(.22, 1, .36, 1), background .18s; }
.interruttore.acceso { background: var(--macchia); box-shadow: none; }
.interruttore.acceso::after { transform: translateX(14px); background: #fff; }
/* nuove segnalazioni: entrano scivolando e restano evidenziate per qualche secondo */
.coda-enter-active { transition: opacity .3s ease-out, transform .35s cubic-bezier(.22, 1, .36, 1); }
.coda-leave-active { transition: opacity .2s ease-in; position: absolute; left: .75rem; right: .75rem; }
.coda-enter-from { opacity: 0; transform: translateX(-12px); }
.coda-leave-to { opacity: 0; }
.coda-move { transition: transform .3s cubic-bezier(.22, 1, .36, 1); }
@keyframes arrivo { from { box-shadow: 0 0 0 1px var(--brace); } to { box-shadow: 0 0 0 1px transparent, 0 0 0 0 transparent; } }
.appena-arrivata { animation: arrivo 3.6s ease-out forwards; }
</style>
