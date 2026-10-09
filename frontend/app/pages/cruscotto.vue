<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { Flame, Check, Ban, Droplets, Leaf, Trash2, Layers, TriangleAlert, Satellite, Wind, Trees, Users, History, Info, MapPin, Clock, Inbox, X, ShieldCheck, Loader2, RotateCw, CircleCheck } from '@lucide/vue'

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
let timer: ReturnType<typeof setInterval> | undefined
let raf = 0

const mostraMappature = ref(false)
const TIPI_MAPPATURA = [
  { codice: 'punto_acqua', etichetta: 'Punto d\'acqua', colore: 'cielo', icona: Droplets },
  { codice: 'sterpaglie', etichetta: 'Sterpaglie secche', colore: 'ambra', icona: Leaf },
  { codice: 'rifiuti_strada', etichetta: 'Rifiuti a bordo strada', colore: 'viola', icona: Trash2 },
] as const
const nMappature = ref(0)
let datiMappature: any = { type: 'FeatureCollection', features: [] }
let datiHotspot: any = { type: 'FeatureCollection', features: [] }

const scheda = computed(() => coda.value.find((s) => s.id === selezionata.value) ?? null)

const ora = (iso: string) => new Date(iso).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'medium' })
const fa = (iso: string) => {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'adesso'
  if (min < 60) return `${min} min fa`
  if (min < 1440) return `${Math.round(min / 60)} h fa`
  return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
}

function iconaMotivo(m: string) {
  const t = m.toLowerCase()
  if (t.includes('hotspot') || t.includes('satellit')) return Satellite
  if (t.includes('meteo') || t.includes('vento')) return Wind
  if (t.includes('suolo')) return Trees
  if (t.includes('pericolo')) return TriangleAlert
  if (t.includes('segnalazion')) return Users
  if (t.includes('storic')) return History
  return Info
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
  (mappa?.getSource('coda') as maplibregl.GeoJSONSource | undefined)?.setData(geojsonCoda())
}

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
      .then((l) => (confermateOggi.value = l.filter((s) => new Date(s.creata_il).toDateString() === oggi).length))
      .catch(() => {})
  } catch { errore.value = 'Connessione persa' }
}

watch(selezionata, aggiornaMappa)
watch(mostraMappature, (v) => mappa?.setLayoutProperty('mappature', 'visibility', v ? 'visible' : 'none'))
watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))

// sorgenti e layer: richiamata a ogni stile caricato (anche dopo il cambio tema)
function aggiungiLivelli() {
  const m = mappa
  if (!m || m.getSource('coda')) return
  const c = coloriMappa(tema.value)
  const prio: any = ['step', ['get', 'priorita'], c.macchia, 30, c.ambra, 60, c.brace]
  m.addSource('hotspot', { type: 'geojson', data: datiHotspot })
  m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 5, 'circle-color': c.brace, 'circle-opacity': 0.9, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 1.5 } })
  m.addSource('mappature', { type: 'geojson', data: datiMappature })
  m.addLayer({ id: 'mappature', type: 'circle', source: 'mappature', layout: { visibility: mostraMappature.value ? 'visible' : 'none' }, paint: {
    'circle-radius': 6,
    'circle-color': ['match', ['get', 'codice'], ...TIPI_MAPPATURA.flatMap((t) => [t.codice, c[t.colore]]), c.testo] as any,
    'circle-stroke-color': c.bordo, 'circle-stroke-width': 2,
  } })
  m.addSource('coda', { type: 'geojson', data: geojsonCoda() })
  m.addLayer({ id: 'coda-alone', type: 'circle', source: 'coda', paint: { 'circle-radius': 14, 'circle-color': prio, 'circle-opacity': 0.3, 'circle-blur': 0.4 } })
  m.addLayer({ id: 'coda', type: 'circle', source: 'coda', paint: {
    'circle-radius': ['case', ['==', ['get', 'selezionata'], 1], 12, 8],
    'circle-color': prio,
    'circle-stroke-color': ['case', ['==', ['get', 'selezionata'], 1], c.testo, c.bordo],
    'circle-stroke-width': ['case', ['==', ['get', 'selezionata'], 1], 3, 2],
  } })
}

// pulsazione lenta dell'alone delle segnalazioni nuove (spenta con reduced-motion)
function pulsa(t: number) {
  if (mappa?.getLayer('coda-alone')) {
    const k = (t % 2600) / 2600
    mappa.setPaintProperty('coda-alone', 'circle-radius', 9 + k * 18)
    mappa.setPaintProperty('coda-alone', 'circle-opacity', 0.45 * (1 - k))
  }
  raf = requestAnimationFrame(pulsa)
}

onMounted(() => {
  registraPmtiles()
  mappa = new maplibregl.Map({ container: contenitore.value!, style: stileMappa(tema.value), center: [9.0, 40.1], zoom: 7.4, minZoom: 6, attributionControl: false, locale: LOCALE_MAPPA })
  // la colonna della coda copre la sinistra: il centro utile della mappa si sposta a destra
  mappa.setPadding({ left: 400, top: 80, right: 0, bottom: 0 })
  mappa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
  mappa.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')
  mappa.on('style.load', aggiungiLivelli)
  // Fuori da 'load': lo strato si crea su style.load e prende datiMappature da qui.
  chiama<any>('/mappature').then((g) => { datiMappature = g; nMappature.value = g.features.length; (mappa?.getSource('mappature') as maplibregl.GeoJSONSource | undefined)?.setData(g) }).catch(() => {})
  chiudiAttribuzione(mappa)
  mappa.on('load', () => {
    const m = mappa!
    m.on('click', 'mappature', (ev) => {
      const p = ev.features?.[0]?.properties
      if (p) new maplibregl.Popup().setLngLat(ev.lngLat).setHTML(`<div style="font-weight:650">${p.titolo}</div><div style="color:var(--testo-2)">${p.utente}</div><div style="color:var(--testo-3);font-size:12px">${ora(p.completata_il)}</div>`).addTo(m)
    })
    m.on('click', 'coda', (ev) => { selezionata.value = ev.features?.[0]?.properties?.id ?? null })
    m.on('mouseenter', 'coda', () => (m.getCanvas().style.cursor = 'pointer'))
    m.on('mouseleave', 'coda', () => (m.getCanvas().style.cursor = ''))
    chiama<any>('/hotspot').then((g) => { datiHotspot = g; (m.getSource('hotspot') as maplibregl.GeoJSONSource | undefined)?.setData(g) }).catch(() => {})
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) raf = requestAnimationFrame(pulsa)
  })
  aggiorna()
  timer = setInterval(aggiorna, 3000)
})

onBeforeUnmount(() => { clearInterval(timer); clearTimeout(tAvviso); cancelAnimationFrame(raf); mappa?.remove() })

function seleziona(s: Segnalazione) {
  selezionata.value = s.id
  mappa?.flyTo({ center: [s.lon, s.lat], zoom: Math.max(mappa.getZoom(), 11), padding: { left: 400, right: 420, top: 80, bottom: 0 } })
}

async function azione(tipo: 'conferma' | 'archivia') {
  if (!scheda.value || inAzione.value) return
  const id = scheda.value.id
  inAzione.value = tipo
  try {
    await chiama(`/segnalazioni/${id}/${tipo}`, { method: 'POST' })
    selezionata.value = null
    mostraAvviso(tipo === 'conferma' ? `Segnalazione #${id} confermata` : `Segnalazione #${id} archiviata come falso allarme`)
    await aggiorna()
  } catch (e) { mostraAvviso(messaggioErrore(e, tipo === 'conferma' ? 'confermare la segnalazione' : 'archiviare la segnalazione'), 'errore') }
  inAzione.value = null
}

const nCoda = useConteggio(() => coda.value.length)
const nConfermate = useConteggio(() => confermateOggi.value)
const nMappe = useConteggio(() => nMappature.value)
const contatori = computed(() => [
  { etichetta: 'In coda', valore: nCoda.value, colore: coda.value.length ? 'var(--brace)' : 'var(--testo)', icona: Inbox },
  { etichetta: 'Confermate oggi', valore: nConfermate.value, colore: 'var(--testo)', icona: Check },
  { etichetta: 'Mappature', valore: nMappe.value, colore: 'var(--testo)', icona: MapPin },
])
</script>

<template>
  <main class="relative h-dvh overflow-hidden">
    <div class="absolute inset-0"><div ref="contenitore" class="h-full w-full" /></div>

    <!-- barra superiore: marchio, stato, contatori -->
    <header class="pointer-events-none absolute inset-x-4 top-4 z-20 flex items-center gap-3">
      <NuxtLink to="/" class="pillola pointer-events-auto flex h-14 items-center gap-3 pr-5 pl-2">
        <span class="flex size-10 items-center justify-center rounded-full bg-gradient-to-br from-[#ff9a3d] to-[#d92d17] shadow-[0_0_20px_rgba(255,106,43,.45)]"><Flame class="size-5 text-white" aria-hidden="true" /></span>
        <span class="leading-tight">
          <span class="block font-semibold">Sentinelle</span>
          <span class="etichetta block !text-[.58rem]">Sala operativa</span>
        </span>
      </NuxtLink>

      <div class="pillola pointer-events-auto flex h-14 items-center gap-1 px-2">
        <div v-for="c in contatori" :key="c.etichetta" class="flex items-center gap-2.5 rounded-full px-3 py-1">
          <component :is="c.icona" class="size-4 text-testo-3" aria-hidden="true" />
          <span class="cifre text-2xl font-bold leading-none" :style="{ color: c.colore }">{{ c.valore }}</span>
          <span class="max-w-[5.5rem] text-[.72rem] leading-tight text-testo-2">{{ c.etichetta }}</span>
        </div>
      </div>

      <span v-if="!errore" class="pillola pointer-events-auto flex h-9 items-center gap-2 px-3 text-[.74rem] text-testo-2" role="status">
        <span class="relative flex size-2">
          <span class="pulsa absolute inset-0 rounded-full bg-macchia" />
          <span class="relative size-2 rounded-full bg-macchia" />
        </span>
        In diretta · ogni 3 s
      </span>
      <button v-else type="button" class="pillola pointer-events-auto flex h-9 items-center gap-2 !border-ambra/50 px-3 text-[.74rem] text-testo-2" role="status" aria-label="Connessione persa: riprova adesso" @click="aggiorna">
        <span class="size-2 rounded-full bg-ambra" aria-hidden="true" />
        <span><span class="font-semibold text-testo">Connessione persa</span> · riprovo da solo</span>
        <RotateCw class="size-3.5 text-testo-3" aria-hidden="true" />
      </button>

      <InterruttoreTema class="pointer-events-auto ml-auto" />
    </header>

    <!-- colonna della coda -->
    <aside class="vetro absolute top-[5.5rem] bottom-4 left-4 z-10 flex w-[23rem] flex-col !bg-[var(--vetro-mappa)] shadow-[var(--ombra-pillola)]" aria-label="Coda delle segnalazioni">
      <div class="flex items-baseline justify-between px-4 pt-4 pb-2">
        <h1 class="text-lg font-semibold tracking-tight">Coda segnalazioni</h1>
        <span v-if="!caricamento" class="etichetta cifre">{{ coda.length }} {{ coda.length === 1 ? 'nuova' : 'nuove' }}</span>
      </div>
      <div v-if="caricamento && errore" class="px-3"><StatoErrore compatto messaggio="Non riusciamo a raggiungere il servizio. La coda si aggiorna da sola appena torna la connessione." @riprova="aggiorna" /></div>
      <ul v-else-if="caricamento" class="flex-1 space-y-1.5 px-2 pb-2" aria-busy="true" aria-label="Caricamento della coda">
        <li v-for="k in 5" :key="k" class="flex items-center gap-3 px-3 py-2.5">
          <span class="scheletro size-[46px] shrink-0 !rounded-full" />
          <span class="flex-1 space-y-2"><span class="scheletro block h-3.5 w-28" /><span class="scheletro block h-2.5 w-20" /></span>
          <span class="scheletro h-3 w-9" />
        </li>
      </ul>
      <div v-else-if="!coda.length" class="flex flex-1 flex-col items-center justify-center gap-3 px-8 pb-16 text-center">
        <span class="flex size-14 items-center justify-center rounded-full bg-macchia/12 text-macchia ring-1 ring-macchia/25"><ShieldCheck class="size-7" aria-hidden="true" /></span>
        <div class="space-y-1">
          <p class="font-semibold">Tutto tranquillo</p>
          <p class="text-[.84rem] text-testo-2">Nessuna segnalazione da valutare. Le nuove compaiono qui da sole, ordinate per priorità.</p>
        </div>
      </div>
      <TransitionGroup v-else tag="ul" name="coda" class="relative flex-1 space-y-1.5 overflow-y-auto px-2 pb-2">
        <li v-for="s in coda" :key="s.id">
          <button
            class="flex w-full items-center gap-3 rounded-[var(--radius-m)] border px-3 py-2.5 text-left transition-colors"
            :class="[s.id === selezionata ? 'border-bordo-luce bg-vetro-forte' : 'border-transparent hover:bg-vetro', appena.has(s.id) && 'appena-arrivata']"
            :aria-current="s.id === selezionata ? 'true' : undefined"
            @click="seleziona(s)"
          >
            <AnelloPriorita :valore="s.priorita" :dimensione="46" />
            <span class="min-w-0 flex-1 leading-tight">
              <span class="flex items-center gap-1.5 font-semibold">
                <Flame v-if="s.tipo === 'fuoco'" class="size-3.5 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-3.5 text-ambra" aria-hidden="true" />
                {{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}
              </span>
              <span class="cifre mt-0.5 flex items-center gap-1 text-[.74rem] text-testo-2"><Clock class="size-3" aria-hidden="true" /> {{ fa(s.creata_il) }} · #{{ s.id }}</span>
            </span>
            <span class="text-[.72rem] font-semibold" :style="{ color: varPriorita(s.priorita) }">{{ etichettaPriorita(s.priorita) }}</span>
          </button>
        </li>
      </TransitionGroup>
    </aside>

    <!-- scheda della segnalazione selezionata -->
    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 translate-x-3" leave-active-class="transition duration-150" leave-to-class="opacity-0 translate-x-3">
      <section v-if="scheda" class="sospeso absolute top-[5.5rem] right-4 z-10 flex max-h-[calc(100%-9.5rem)] w-[24rem] flex-col overflow-hidden" aria-labelledby="titolo-scheda">
        <div class="min-h-0 flex-1 space-y-4 overflow-y-auto p-5 pb-4">
          <div class="flex items-start gap-4">
            <AnelloPriorita :valore="scheda.priorita" :dimensione="84" :spessore="2.8" />
            <div class="min-w-0 flex-1">
              <p class="etichetta">Segnalazione #{{ scheda.id }}</p>
              <h2 id="titolo-scheda" class="text-xl font-semibold">{{ scheda.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}</h2>
              <p class="text-sm font-semibold" :style="{ color: varPriorita(scheda.priorita) }">Priorità {{ etichettaPriorita(scheda.priorita).toLowerCase() }}</p>
            </div>
            <button type="button" aria-label="Chiudi la scheda" class="secondario tocco flex size-9 shrink-0 items-center justify-center" @click="selezionata = null"><X class="size-[18px]" /></button>
          </div>
          <p class="cifre flex flex-wrap gap-x-3 gap-y-1 text-[.78rem] text-testo-2">
            <span class="flex items-center gap-1"><Clock class="size-3.5" aria-hidden="true" /> {{ ora(scheda.creata_il) }}</span>
            <span class="flex items-center gap-1"><MapPin class="size-3.5" aria-hidden="true" /> {{ scheda.lat.toFixed(4) }}, {{ scheda.lon.toFixed(4) }}</span>
          </p>
          <a v-if="scheda.foto_url" :href="urlFoto(scheda.foto_url)!" target="_blank" rel="noopener" class="block overflow-hidden rounded-[var(--radius-m)] border border-bordo bg-vetro-forte" aria-label="Apri la foto a dimensione piena">
            <img :key="scheda.id" :src="urlFoto(scheda.foto_url)!" alt="Foto allegata alla segnalazione" class="h-44 w-full object-cover" />
          </a>
          <div>
            <p class="etichetta mb-1.5">Motivazioni</p>
            <ul class="vetro divide-y divide-bordo !p-0 text-[.84rem]">
              <li v-for="m in scheda.motivazioni" :key="m" class="flex items-start gap-3 px-3 py-2">
                <component :is="iconaMotivo(m)" class="mt-0.5 size-4 shrink-0 text-testo-3" aria-hidden="true" />
                <span class="text-testo-2">{{ m }}</span>
              </li>
            </ul>
          </div>
        </div>
        <div class="grid shrink-0 grid-cols-2 gap-2 border-t border-bordo p-4">
          <button class="primario flex h-12 items-center justify-center gap-1.5" :disabled="!!inAzione" @click="azione('conferma')">
            <Loader2 v-if="inAzione === 'conferma'" class="size-5 animate-spin" aria-hidden="true" /><Check v-else class="size-5" aria-hidden="true" /> Conferma
          </button>
          <button class="secondario flex h-12 items-center justify-center gap-1.5" :disabled="!!inAzione" aria-label="Archivia come falso allarme" @click="azione('archivia')">
            <Loader2 v-if="inAzione === 'archivia'" class="size-5 animate-spin" aria-hidden="true" /><Ban v-else class="size-5" aria-hidden="true" /> Falso allarme
          </button>
        </div>
      </section>
    </Transition>

    <!-- legenda e filtri: pillole sopra la mappa -->
    <div class="absolute bottom-4 left-[calc(23rem+2rem)] z-10 flex flex-wrap items-center gap-2 text-[.76rem]">
      <span class="pillola flex h-9 items-center gap-3 px-3.5">
        <span class="etichetta">Priorità</span>
        <span class="flex items-center gap-1.5"><span class="size-2.5 rounded-full bg-alta" />Alta</span>
        <span class="flex items-center gap-1.5"><span class="size-2.5 rounded-full bg-media" />Media</span>
        <span class="flex items-center gap-1.5"><span class="size-2.5 rounded-full bg-bassa" />Bassa</span>
      </span>
      <span class="pillola flex h-9 items-center gap-1.5 px-3.5"><span class="size-2 rounded-full bg-brace ring-2 ring-fondo" /> Hotspot satellitari</span>
      <button type="button" class="pillola flex h-9 items-center gap-1.5 px-3.5 font-semibold transition-colors" :class="mostraMappature ? '!border-macchia/50 text-testo' : 'text-testo-2'" :aria-pressed="mostraMappature" @click="mostraMappature = !mostraMappature">
        <Layers class="size-4" :class="mostraMappature && 'text-macchia'" aria-hidden="true" /> Mappature dei cittadini <span class="cifre text-testo-3">{{ nMappature }}</span>
      </button>
      <span v-if="mostraMappature && !nMappature" class="pillola flex h-9 items-center px-3.5 text-testo-2">Ancora nessuna mappatura: arrivano dalle missioni dei cittadini</span>
      <template v-else-if="mostraMappature">
        <span v-for="t in TIPI_MAPPATURA" :key="t.codice" class="pillola flex h-9 items-center gap-1.5 px-3">
          <component :is="t.icona" class="size-3.5" :style="{ color: t.colore === 'viola' ? '#b48cf2' : `var(--${t.colore})` }" aria-hidden="true" />{{ t.etichetta }}
        </span>
      </template>
    </div>

    <!-- esito delle azioni dell'operatore -->
    <Transition enter-active-class="transition duration-250 ease-out" enter-from-class="opacity-0 translate-y-2" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0 translate-y-1">
      <div v-if="avviso" :key="avviso.id" class="pointer-events-none absolute bottom-16 left-1/2 z-30 -translate-x-1/2" role="status">
        <span class="sospeso flex items-center gap-2 !rounded-full py-2 pr-4 pl-2.5 text-sm font-semibold">
          <CircleCheck v-if="avviso.tipo === 'ok'" class="size-5 text-macchia" aria-hidden="true" />
          <TriangleAlert v-else class="size-5 text-ambra" aria-hidden="true" />
          {{ avviso.testo }}
        </span>
      </div>
    </Transition>
  </main>
</template>

<style>
/* nuove segnalazioni: entrano scivolando e restano evidenziate per qualche secondo */
.coda-enter-active { transition: opacity .3s ease-out, transform .35s cubic-bezier(.22, 1, .36, 1); }
.coda-leave-active { transition: opacity .2s ease-in; position: absolute; left: .5rem; right: .5rem; }
.coda-enter-from { opacity: 0; transform: translateX(-12px); }
.coda-leave-to { opacity: 0; }
.coda-move { transition: transform .3s cubic-bezier(.22, 1, .36, 1); }
@keyframes arrivo { from { box-shadow: 0 0 0 1px var(--brace), 0 0 22px -4px var(--brace); } to { box-shadow: 0 0 0 1px transparent, 0 0 0 0 transparent; } }
.appena-arrivata { animation: arrivo 3.6s ease-out forwards; }
</style>
