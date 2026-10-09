<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { Flame, X, MapPin, LocateFixed, Camera, Satellite, Wind, Trees, TriangleAlert, Users, History, Info, ChevronRight, Star, Loader2, ArrowLeft } from '@lucide/vue'
import type { Scheda } from '~/components/BarraNavigazione.vue'

const { chiama, urlFoto } = useApi()

const CENTRI = CENTRI_COMUNI

const utenti = ref<Utente[]>([])
const utente = ref<Utente | null>(null)
const rischio = ref<Rischio | null>(null)
const errore = ref('')

const pannello = ref(false)
const tipo = ref<'fuoco' | 'area_a_rischio'>('fuoco')
const foto = ref<File | null>(null)
const pos = ref<{ lat: number; lon: number } | null>(null)
const inCorso = ref(false)
const esito = ref<Segnalazione | null>(null)

const scheda = ref<Scheda>('mappa')
const missione = ref<Missione | null>(null) // missione `posizione` in attesa del punto sulla mappa
const toast = ref<{ id: number; testo: string } | null>(null)
const nuovoLivello = ref<string | null>(null)
let tToast: ReturnType<typeof setTimeout> | undefined
let tLivello: ReturnType<typeof setTimeout> | undefined

const FILTRI = [
  { id: '2025', etichetta: '2025', da: 2025 },
  { id: '5', etichetta: 'Ultimi 5 anni', da: 2021 },
  { id: 'tutti', etichetta: 'Dal 2015', da: 2015 },
] as const
const filtro = ref<(typeof FILTRI)[number]['id']>('2025')

const contenitore = ref<HTMLElement | null>(null)
let mappa: maplibregl.Map | null = null
let marcatore: maplibregl.Marker | null = null

const centro = computed<[number, number]>(() => CENTRI[utente.value?.comune ?? ''] ?? [8.9, 40.1])
const { tema } = useTema()

// icona per ogni motivazione della priorita' (riconosciuta dal testo)
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
const iniziali = (n: string) => n.replace(/\(.*?\)/g, '').trim().split(/\s+/).map((p) => p[0]).join('').slice(0, 2).toUpperCase()

onMounted(async () => {
  try {
    utenti.value = await chiama<Utente[]>('/utenti')
    const salvato = (() => { try { return Number(localStorage.getItem('utenteId')) } catch { return 0 } })()
    const trovato = utenti.value.find((u) => u.id === salvato)
    if (trovato) await scegli(trovato)
  } catch (e: any) { errore.value = 'Server non raggiungibile: ' + e.message }
})

onBeforeUnmount(() => { clearTimeout(tToast); clearTimeout(tLivello); mappa?.remove() })

async function scegli(u: Utente) {
  utente.value = u
  chiama<Utente>(`/utenti/${u.id}`).then((d) => (utente.value = d)).catch(() => {})
  try { localStorage.setItem('utenteId', String(u.id)) } catch {}
  rischio.value = null
  chiama<Rischio>(`/rischio?lat=${centro.value[1]}&lon=${centro.value[0]}`).then((r) => (rischio.value = r)).catch(() => {})
  await nextTick()
  avviaMappa()
}

function cambiaUtente() {
  mappa?.remove(); mappa = null; marcatore = null; datiHotspot = VUOTO
  utente.value = null; pannello.value = false; esito.value = null; missione.value = null; scheda.value = 'mappa'
  try { localStorage.removeItem('utenteId') } catch {}
}

const VUOTO = { type: 'FeatureCollection' as const, features: [] }
let datiHotspot: any = VUOTO

function avviaMappa() {
  if (!contenitore.value) return
  registraPmtiles()
  mappa = new maplibregl.Map({
    container: contenitore.value, style: stileMappa(tema.value), center: centro.value, zoom: 12, minZoom: 6,
    attributionControl: false,
  })
  mappa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
  mappa.addControl(new maplibregl.AttributionControl({ compact: true }), 'top-right')
  // sorgenti e layer si (ri)aggiungono a ogni stile caricato: anche dopo il cambio tema
  mappa.on('style.load', aggiungiLivelli)
  chiudiAttribuzione(mappa)
  mappa.on('load', () => {
    const m = mappa!
    m.on('click', 'storico-riempimento', (ev) => {
      const p = ev.features?.[0]?.properties
      if (!p || pannello.value || missione.value) return
      new maplibregl.Popup({ maxWidth: '220px' }).setLngLat(ev.lngLat)
        .setHTML(`<div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--testo-3);font-weight:650">Incendio ${p.anno}</div><div style="font-weight:650;margin-top:2px">${p.data ?? 'data n.d.'}</div><div style="font-variant-numeric:tabular-nums;color:var(--testo-2)">${p.ettari != null ? Number(p.ettari).toFixed(1) + ' ettari' : 'ettari n.d.'}${p.comune ? ' · ' + p.comune : ''}</div>`)
        .addTo(m)
    })
    m.on('click', (ev) => {
      if (!pannello.value && !missione.value) return
      impostaPos(ev.lngLat.lat, ev.lngLat.lng)
    })
    chiama<any>('/hotspot').then((g) => { datiHotspot = g; (m.getSource('hotspot') as maplibregl.GeoJSONSource | undefined)?.setData(g) }).catch(() => {})
  })
}

function aggiungiLivelli() {
  const m = mappa
  if (!m || m.getSource('storico')) return
  const c = coloriMappa(tema.value)
  m.addSource('storico', { type: 'vector', url: 'pmtiles:///tiles/storico.pmtiles' })
  m.addLayer({ id: 'storico-riempimento', type: 'fill', source: 'storico', 'source-layer': 'incendi', filter: filtroAnni(), paint: { 'fill-color': c.storico, 'fill-opacity': c.opacitaStorico } })
  m.addLayer({ id: 'storico-linea', type: 'line', source: 'storico', 'source-layer': 'incendi', filter: filtroAnni(), paint: { 'line-color': c.storico, 'line-width': 0.7, 'line-opacity': 0.55 } })
  m.addSource('hotspot', { type: 'geojson', data: datiHotspot })
  m.addLayer({ id: 'hotspot-alone', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 16, 'circle-color': c.brace, 'circle-opacity': 0.18, 'circle-blur': 0.6 } })
  m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 6, 'circle-color': c.brace, 'circle-stroke-color': c.bordo, 'circle-stroke-width': 2 } })
}

watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))

const filtroAnni = () => ['>=', ['get', 'anno'], FILTRI.find((f) => f.id === filtro.value)!.da] as any

// filtro anni istantaneo: i dati sono gia' nei tile
watch(filtro, () => { for (const id of ['storico-riempimento', 'storico-linea']) if (mappa?.getLayer(id)) mappa.setFilter(id, filtroAnni()) })

function impostaPos(lat: number, lon: number) {
  pos.value = { lat, lon }
  if (!mappa) return
  if (!marcatore) {
    const el = document.createElement('div')
    el.className = 'segnaposto'
    el.innerHTML = '<span></span><i></i>'
    marcatore = new maplibregl.Marker({ element: el, anchor: 'center' })
  }
  marcatore.setLngLat([lon, lat]).addTo(mappa)
}

function usaGps() {
  errore.value = ''
  navigator.geolocation.getCurrentPosition(
    (p) => { impostaPos(p.coords.latitude, p.coords.longitude); mappa?.flyTo({ center: [p.coords.longitude, p.coords.latitude], zoom: 15 }) },
    () => (errore.value = 'GPS non disponibile: tocca la mappa per scegliere il punto'),
    { enableHighAccuracy: true, timeout: 8000 },
  )
}

async function apri() {
  esito.value = null; pos.value = null; foto.value = null; errore.value = ''
  marcatore?.remove()
  pannello.value = true
  await nextTick(); mappa?.resize()
}

async function chiudi() {
  pannello.value = false; marcatore?.remove(); pos.value = null
  await nextTick(); mappa?.resize()
}

// aggiorna header e mostra toast/overlay dopo un'azione che da' punti
function applicaEsito(r: { punti_ottenuti: number; punti: number; livello: Livello }) {
  if (!utente.value) return
  const vecchio = utente.value.livello?.nome
  utente.value = { ...utente.value, punti: r.punti, livello: r.livello }
  if (r.punti_ottenuti > 0) {
    toast.value = { id: Date.now(), testo: `+${r.punti_ottenuti} punti` }
    clearTimeout(tToast); tToast = setTimeout(() => (toast.value = null), 2500)
  }
  if (vecchio && vecchio !== r.livello.nome) {
    nuovoLivello.value = r.livello.nome
    clearTimeout(tLivello); tLivello = setTimeout(() => (nuovoLivello.value = null), 3000)
  }
}

watch(scheda, async (s) => {
  if (s === 'mappa') { await nextTick(); mappa?.resize() }
})

// missione `posizione`: passa alla mappa in modalita' "scegli punto"
async function scegliPunto(m: Missione) {
  missione.value = m; pos.value = null; foto.value = null; errore.value = ''
  marcatore?.remove(); pannello.value = false
  scheda.value = 'mappa'
  await nextTick(); mappa?.resize()
}

async function annullaMissione() {
  missione.value = null; pos.value = null; marcatore?.remove(); errore.value = ''
  scheda.value = 'missioni'
}

async function confermaMissione() {
  if (!utente.value || !pos.value || !missione.value) return
  inCorso.value = true; errore.value = ''
  const f = new FormData()
  f.append('utente_id', String(utente.value.id))
  f.append('lat', String(pos.value.lat))
  f.append('lon', String(pos.value.lon))
  if (foto.value) f.append('foto', foto.value)
  try {
    const r = await chiama<EsitoMissione>(`/missioni/${missione.value.id}/completa`, { method: 'POST', body: f })
    marcatore?.remove(); pos.value = null; missione.value = null
    scheda.value = 'missioni'
    applicaEsito(r)
  } catch (e: any) {
    errore.value = String(e.message).startsWith('409') ? 'Hai raggiunto il limite di oggi per questa missione.' : 'Invio non riuscito: ' + e.message
  }
  inCorso.value = false
}

async function invia() {
  if (!utente.value || !pos.value) return
  inCorso.value = true; errore.value = ''
  const f = new FormData()
  f.append('utente_id', String(utente.value.id))
  f.append('tipo', tipo.value)
  f.append('lat', String(pos.value.lat))
  f.append('lon', String(pos.value.lon))
  if (foto.value) f.append('foto', foto.value)
  try {
    esito.value = await chiama<Segnalazione>('/segnalazioni', { method: 'POST', body: f })
    if (esito.value.punti_ottenuti > 0) {
      const d = await chiama<Utente>(`/utenti/${utente.value.id}`)
      applicaEsito({ punti_ottenuti: esito.value.punti_ottenuti, punti: d.punti, livello: d.livello! })
    }
  } catch (e: any) { errore.value = 'Invio non riuscito: ' + e.message }
  inCorso.value = false
}
</script>

<template>
  <main class="relative h-dvh overflow-hidden">
    <!-- scelta utente: schermata d'ingresso -->
    <section v-if="!utente" class="mx-auto flex h-dvh max-w-md flex-col overflow-y-auto px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-8">
      <div class="flex items-center justify-between">
        <NuxtLink to="/" class="pillola flex size-10 items-center justify-center" aria-label="Torna all'inizio"><ArrowLeft class="size-[18px] text-testo-2" /></NuxtLink>
        <InterruttoreTema />
      </div>

      <div class="mt-10 flex flex-col items-center text-center">
        <span class="relative flex size-20 items-center justify-center">
          <span class="absolute inset-0 rounded-full bg-[radial-gradient(closest-side,rgba(255,106,43,.45),transparent)] blur-md" aria-hidden="true" />
          <span class="relative flex size-16 items-center justify-center rounded-[22px] bg-gradient-to-br from-[#ff9a3d] to-[#d92d17] shadow-[0_12px_30px_-8px_rgba(255,90,31,.6),inset_0_1px_0_rgba(255,255,255,.3)]">
            <Flame class="size-9 text-white" aria-hidden="true" />
          </span>
        </span>
        <h1 class="mt-5 font-[family-name:var(--font-display)] text-[2.1rem] font-bold tracking-tight">Sentinelle</h1>
        <p class="mt-1.5 max-w-[17rem] text-[.95rem] text-testo-2">Occhi accesi sulla Sardegna. Segnala, previeni, proteggi il tuo comune.</p>
      </div>

      <p class="etichetta mt-10 mb-2.5 px-1">Chi sei?</p>
      <p v-if="errore" class="mb-3 flex items-center gap-2 rounded-[var(--radius-m)] border border-brace/40 bg-brace/10 p-3 text-sm text-brace" role="alert"><TriangleAlert class="size-4 shrink-0" /> {{ errore }}</p>
      <ul class="vetro divide-y divide-bordo overflow-hidden !p-0">
        <li v-for="u in utenti" :key="u.id">
          <button class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-vetro-forte active:bg-vetro-forte" @click="scegli(u)">
            <span class="flex size-10 shrink-0 items-center justify-center rounded-full bg-vetro-forte text-[.8rem] font-bold ring-1 ring-bordo-luce">{{ iniziali(u.nome) }}</span>
            <span class="min-w-0 flex-1 leading-tight">
              <span class="block truncate font-semibold">{{ u.nome }}</span>
              <span class="block text-[.78rem] capitalize text-testo-2">{{ u.comune.toLowerCase() }}</span>
            </span>
            <span class="cifre flex items-center gap-1 text-[.9rem] font-semibold"><Star class="size-3.5 fill-ambra text-ambra" aria-hidden="true" />{{ u.punti }}</span>
            <ChevronRight class="size-4 text-testo-3" aria-hidden="true" />
          </button>
        </li>
        <li v-if="!utenti.length && !errore" class="flex items-center justify-center gap-2 p-6 text-sm text-testo-2"><Loader2 class="size-4 animate-spin" /> Caricamento…</li>
      </ul>
    </section>

    <template v-else>
      <!-- la mappa sta sotto tutto, sempre -->
      <div class="mappa-app absolute inset-0"><div ref="contenitore" class="h-full w-full" /></div>

      <!-- header: pillole fluttuanti -->
      <header class="pointer-events-none absolute inset-x-0 top-0 z-20 px-3 pt-[max(.75rem,env(safe-area-inset-top))]">
        <div class="flex items-start gap-2">
          <button type="button" class="pillola pointer-events-auto flex h-12 min-w-0 flex-1 items-center pr-3 pl-1 text-left" aria-label="Il tuo profilo: tocca per cambiare utente" @click="cambiaUtente">
            <IndicatoreLivello :nome="utente.nome" :punti="utente.punti" :livello="utente.livello" />
          </button>
          <IndicatoreRischio class="pointer-events-auto" :rischio="rischio" />
          <InterruttoreTema compatto class="pointer-events-auto" />
        </div>
        <div v-if="scheda === 'mappa' && !missione" class="mt-2 flex items-center gap-2">
          <div class="pillola pointer-events-auto flex items-center gap-0.5 p-1 text-[.76rem]" role="group" aria-label="Incendi storici">
            <button v-for="f in FILTRI" :key="f.id" type="button" class="h-8 rounded-full px-3 font-semibold transition-colors" :class="filtro === f.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2'" :aria-pressed="filtro === f.id" @click="filtro = f.id">{{ f.etichetta }}</button>
          </div>
        </div>
      </header>

      <!-- missione `posizione`: scegli il punto -->
      <Transition name="foglio">
        <section v-if="scheda === 'mappa' && missione" class="sospeso fixed inset-x-2 bottom-[5.5rem] z-20 space-y-3 p-4">
          <div>
            <p class="etichetta">Missione · +{{ missione.punti }} punti</p>
            <p class="mt-0.5 text-lg font-semibold">{{ missione.titolo }}</p>
          </div>
          <p class="flex items-center gap-2 rounded-[var(--radius-m)] border p-3 text-sm" :class="pos ? 'border-macchia/40 bg-macchia/10 font-semibold text-macchia' : 'border-bordo bg-vetro text-testo-2'">
            <MapPin class="size-4 shrink-0" aria-hidden="true" />
            <span class="cifre">{{ pos ? `Punto scelto: ${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}` : 'Tocca la mappa per indicare il punto' }}</span>
          </p>
          <div class="grid grid-cols-2 gap-2">
            <button type="button" class="secondario flex h-11 items-center justify-center gap-1.5 text-sm" @click="usaGps"><LocateFixed class="size-4" aria-hidden="true" /> Usa GPS</button>
            <label class="secondario flex h-11 items-center justify-center gap-1.5 border-dashed px-3 text-sm">
              <Camera class="size-4 shrink-0 text-testo-2" aria-hidden="true" /><span class="truncate">{{ foto ? foto.name : 'Foto' }}</span>
              <input type="file" accept="image/*" capture="environment" class="sr-only" @change="foto = ($event.target as HTMLInputElement).files?.[0] ?? null" />
            </label>
          </div>
          <p v-if="errore" class="text-sm text-brace" role="alert">{{ errore }}</p>
          <div class="grid grid-cols-[auto_1fr] gap-2">
            <button type="button" class="secondario h-12 px-5" @click="annullaMissione">Annulla</button>
            <button type="button" class="primario h-12" :disabled="!pos || inCorso" @click="confermaMissione">{{ inCorso ? 'Invio…' : `Conferma · +${missione.punti}` }}</button>
          </div>
        </section>
      </Transition>

      <!-- l'unico accento pieno -->
      <Transition name="foglio">
        <button v-if="scheda === 'mappa' && !pannello && !missione" type="button" class="primario fixed bottom-[5.75rem] left-1/2 z-20 flex h-14 w-[min(19rem,calc(100%-2.5rem))] -translate-x-1/2 items-center justify-center gap-2 text-lg" @click="apri">
          <Flame class="size-6" aria-hidden="true" /> Segnala
        </button>
      </Transition>

      <!-- segnalazione ed esito -->
      <Transition name="foglio">
        <section v-if="scheda === 'mappa' && pannello && !missione" class="sospeso fixed inset-x-2 bottom-[5.5rem] z-20 max-h-[62dvh] overflow-y-auto p-4" aria-labelledby="titolo-pannello">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="etichetta">{{ esito ? 'Segnalazione inviata' : 'Nuova segnalazione' }}</p>
              <h2 id="titolo-pannello" class="mt-0.5 text-lg font-semibold">{{ esito ? 'Grazie, è in coda agli operatori' : 'Cosa vedi?' }}</h2>
            </div>
            <button type="button" aria-label="Chiudi" class="secondario flex size-9 shrink-0 items-center justify-center" @click="chiudi"><X class="size-[18px]" /></button>
          </div>

          <!-- esito -->
          <div v-if="esito" class="space-y-4">
            <div class="flex items-center gap-4">
              <AnelloPriorita :valore="esito.priorita" :dimensione="104" :spessore="2.6" />
              <div class="min-w-0">
                <p class="etichetta">Priorità stimata</p>
                <p class="text-2xl font-bold" :style="{ color: varPriorita(esito.priorita) }">{{ etichettaPriorita(esito.priorita) }}</p>
                <p v-if="esito.punti_ottenuti > 0" class="cifre mt-1.5 inline-flex items-center gap-1 rounded-full bg-ambra/15 px-2.5 py-1 text-[.8rem] font-semibold text-ambra"><Star class="size-3.5 fill-current" aria-hidden="true" /> +{{ esito.punti_ottenuti }} punti</p>
              </div>
            </div>
            <div>
              <p class="etichetta mb-1.5">Perché questa priorità</p>
              <ul class="vetro divide-y divide-bordo !p-0 text-[.86rem]">
                <li v-for="m in esito.motivazioni" :key="m" class="flex items-start gap-3 px-3 py-2.5">
                  <component :is="iconaMotivo(m)" class="mt-0.5 size-4 shrink-0 text-testo-3" aria-hidden="true" />
                  <span class="text-testo-2">{{ m }}</span>
                </li>
              </ul>
            </div>
            <button type="button" class="secondario h-12 w-full" @click="chiudi">Fatto</button>
          </div>

          <!-- modulo -->
          <form v-else class="space-y-3" @submit.prevent="invia">
            <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Tipo di segnalazione">
              <button type="button" role="radio" :aria-checked="tipo === 'fuoco'" class="flex flex-col items-start gap-2 rounded-[var(--radius-m)] border p-3 text-left transition-colors" :class="tipo === 'fuoco' ? 'border-brace/60 bg-brace/12 ring-1 ring-brace/40' : 'border-bordo bg-vetro'" @click="tipo = 'fuoco'">
                <Flame class="size-6" :class="tipo === 'fuoco' ? 'text-brace' : 'text-testo-3'" aria-hidden="true" />
                <span class="text-[.92rem] font-semibold leading-tight">Fuoco o fumo</span>
                <span class="text-[.72rem] text-testo-2">Lo vedi adesso</span>
              </button>
              <button type="button" role="radio" :aria-checked="tipo === 'area_a_rischio'" class="flex flex-col items-start gap-2 rounded-[var(--radius-m)] border p-3 text-left transition-colors" :class="tipo === 'area_a_rischio' ? 'border-ambra/60 bg-ambra/12 ring-1 ring-ambra/40' : 'border-bordo bg-vetro'" @click="tipo = 'area_a_rischio'">
                <TriangleAlert class="size-6" :class="tipo === 'area_a_rischio' ? 'text-ambra' : 'text-testo-3'" aria-hidden="true" />
                <span class="text-[.92rem] font-semibold leading-tight">Area a rischio</span>
                <span class="text-[.72rem] text-testo-2">Sterpaglie, rifiuti…</span>
              </button>
            </div>

            <div class="flex items-center gap-2 rounded-[var(--radius-m)] border p-1.5 pl-3" :class="pos ? 'border-macchia/40 bg-macchia/10' : 'border-bordo bg-vetro'">
              <MapPin class="size-4 shrink-0" :class="pos ? 'text-macchia' : 'text-testo-3'" aria-hidden="true" />
              <span class="cifre min-w-0 flex-1 text-[.82rem] leading-tight" :class="pos ? 'font-semibold text-macchia' : 'text-testo-2'">
                {{ pos ? `${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}` : 'Tocca la mappa per indicare il punto' }}
              </span>
              <button type="button" class="secondario flex h-9 shrink-0 items-center gap-1.5 px-3 text-[.8rem]" @click="usaGps"><LocateFixed class="size-4" aria-hidden="true" /> GPS</button>
            </div>

            <label class="flex items-center gap-3 rounded-[var(--radius-m)] border border-dashed border-bordo-luce bg-vetro p-3 text-sm">
              <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-vetro-forte"><Camera class="size-[18px] text-testo-2" aria-hidden="true" /></span>
              <span class="min-w-0 leading-tight">
                <span class="block truncate font-semibold">{{ foto ? foto.name : 'Aggiungi una foto' }}</span>
                <span class="block text-[.72rem] text-testo-2">{{ foto ? 'Tocca per cambiarla' : 'Facoltativa, aiuta gli operatori' }}</span>
              </span>
              <input type="file" accept="image/*" capture="environment" class="sr-only" @change="foto = ($event.target as HTMLInputElement).files?.[0] ?? null" />
            </label>

            <p v-if="errore" class="text-sm text-brace" role="alert">{{ errore }}</p>
            <button class="primario flex h-14 w-full items-center justify-center gap-2 text-lg" :disabled="!pos || inCorso">
              <Loader2 v-if="inCorso" class="size-5 animate-spin" aria-hidden="true" />{{ inCorso ? 'Invio…' : 'Invia segnalazione' }}
            </button>
          </form>
        </section>
      </Transition>

      <!-- missioni e classifica: fogli sopra la mappa -->
      <Transition name="foglio">
        <section v-if="scheda === 'missioni'" class="sospeso fixed inset-x-2 top-[calc(max(.75rem,env(safe-area-inset-top))+3.75rem)] bottom-[5.5rem] z-20 overflow-y-auto">
          <SchedaMissioni :utente="utente" @esito="applicaEsito" @posizione="scegliPunto" />
        </section>
      </Transition>
      <Transition name="foglio">
        <section v-if="scheda === 'classifica'" class="sospeso fixed inset-x-2 top-[calc(max(.75rem,env(safe-area-inset-top))+3.75rem)] bottom-[5.5rem] z-20 overflow-y-auto">
          <SchedaClassifica :comune="utente.comune" :nome-utente="utente.nome" />
        </section>
      </Transition>

      <BarraNavigazione v-model="scheda" />
      <ToastPunti :toast="toast" :nuovo-livello="nuovoLivello" />
    </template>
  </main>
</template>

<style>
.mappa-app .maplibregl-ctrl-top-right { top: calc(max(.75rem, env(safe-area-inset-top)) + 6.5rem); right: 2px; }
.foglio-enter-active, .foglio-leave-active { transition: opacity .22s ease, transform .22s ease; }
.foglio-enter-from, .foglio-leave-to { opacity: 0; transform: translateY(12px); }
.segnaposto { position: relative; width: 22px; height: 22px; }
.segnaposto span { position: absolute; inset: 0; border-radius: 999px; background: linear-gradient(135deg, #ff9a3d, #e8351f); border: 3px solid var(--fondo-3); box-shadow: 0 0 0 1px rgba(0,0,0,.25), 0 0 18px rgba(255,106,43,.7); }
.segnaposto i { position: absolute; inset: -10px; border-radius: 999px; border: 2px solid #ff6a2b; animation: pulsa 2.4s ease-in-out infinite; }
</style>
