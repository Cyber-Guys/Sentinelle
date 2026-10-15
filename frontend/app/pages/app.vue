<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { aggiungiHotspot, aggiungiPinSegnalazioni, geojsonSegnalazioni, aloneSegnalazioni, animaAloni, apriPopup, ALONE_HOTSPOT, FILTRI_STORICO_INCENDI as FILTRI, aggiungiStoricoIncendi, impostaStoricoIncendi, clicIncendio, clicHotspot, type Alone } from '~/composables/useMappa'
import PopupSegnalazione from '~/components/PopupSegnalazione.vue'
import { Flame, X, MapPin, LocateFixed, Camera, TriangleAlert, ChevronRight, Star, Loader2, ArrowLeft, CircleCheck } from '@lucide/vue'
import type { Scheda } from '~/components/BarraNavigazione.vue'

const { chiama, urlFoto } = useApi()

const CENTRI = CENTRI_COMUNI

const utenti = ref<Utente[]>([])
const utente = ref<Utente | null>(null)
const rischio = ref<Rischio | null>(null)
const rischioErrore = ref(false)
const errore = ref('')
const caricamentoUtenti = ref(true)
const erroreUtenti = ref('')

const pannello = ref(false)
const tipo = ref<'fuoco' | 'area_a_rischio'>('fuoco')
const foto = ref<File | null>(null)
const pos = ref<{ lat: number; lon: number } | null>(null)
const inCorso = ref(false)
const esito = ref<Segnalazione | null>(null)

const scheda = ref<Scheda>('mappa')
const missione = ref<Missione | null>(null) // missione `posizione` in attesa del punto sulla mappa
const toast = ref<{ id: number; testo: string; nota?: string; esito?: 'ok' | 'no' } | null>(null)
const nuovoLivello = ref<{ nome: string; punti: number } | null>(null)
let tToast: ReturnType<typeof setTimeout> | undefined
let tLivello: ReturnType<typeof setTimeout> | undefined

const filtro = ref<string>('2025')

// proprie segnalazioni: pin sempre sulla mappa, elenco nella scheda, polling leggero dello stato
const mie = ref<Segnalazione[]>([])
const mieCaricamento = ref(true)
const mieErrore = ref('')
const mieNovita = ref(false) // pallino sulla voce Segnalazioni dopo una valutazione
let note: Map<number, Segnalazione> | null = null // stato al fetch precedente: null = primo caricamento, niente toast
let tMie: ReturnType<typeof setInterval> | undefined
let popupMia: maplibregl.Popup | null = null
let popupMiaId = 0

const contenitore = ref<HTMLElement | null>(null)
let mappa: maplibregl.Map | null = null
const mappaPronta = shallowRef<maplibregl.Map | null>(null) // per ControlliMappa
let marcatore: maplibregl.Marker | null = null
let fermaAloni = () => {}

const centro = computed<[number, number]>(() => CENTRI[utente.value?.comune ?? ''] ?? [8.9, 40.1])
const { tema } = useTema()

const oraBreve = (iso: string) => new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
const iniziali = (n: string) => n.replace(/\(.*?\)/g, '').trim().split(/\s+/).map((p) => p[0]).join('').slice(0, 2).toUpperCase()

async function caricaUtenti() {
  caricamentoUtenti.value = true; erroreUtenti.value = ''
  try {
    utenti.value = await chiama<Utente[]>('/utenti')
    const salvato = (() => { try { return Number(localStorage.getItem('utenteId')) } catch { return 0 } })()
    const trovato = utenti.value.find((u) => u.id === salvato)
    if (trovato) await scegli(trovato)
  } catch (e) { erroreUtenti.value = messaggioErrore(e, 'caricare le sentinelle') }
  caricamentoUtenti.value = false
}
onMounted(caricaUtenti)
const eventi = useEventi()
const fermaEventi = [
  eventi.on('segnalazione_valutata', (d) => { if (d.utente_id === utente.value?.id) caricaMie() }),
  eventi.on('hotspot_aggiornati', () => { if (mappa) caricaHotspot() }),
]

onBeforeUnmount(() => { fermaEventi.forEach((f) => f()); clearTimeout(tToast); clearTimeout(tLivello); clearInterval(tMie); fermaAloni(); mappa?.remove() })

async function scegli(u: Utente) {
  utente.value = u
  chiama<Utente>(`/utenti/${u.id}`).then((d) => (utente.value = d)).catch(() => {})
  try { localStorage.setItem('utenteId', String(u.id)) } catch {}
  caricaRischio()
  caricaMie()
  clearInterval(tMie); tMie = setInterval(caricaMie, 30000) // rete di sicurezza: gli eventi SSE aggiornano subito
  await nextTick()
  avviaMappa()
}

async function caricaMie() {
  const u = utente.value
  if (!u) return
  try {
    const l = await chiama<Segnalazione[]>(`/segnalazioni?stato=tutte&utente_id=${u.id}`)
    if (utente.value?.id !== u.id) return
    const prima = note
    const valutate = prima ? l.filter((s) => prima.get(s.id)?.stato === 'nuova' && s.stato !== 'nuova') : []
    note = new Map(l.map((s) => [s.id, s]))
    mie.value = l; mieErrore.value = ''
    aggiornaPinMie()
    if (prima && valutate.length) {
      // popup aperto su una segnalazione appena valutata: si riapre col nuovo stato
      const aperta = popupMia?.isOpen() && valutate.find((x) => x.id === popupMiaId)
      if (aperta) apriPopupMia(aperta)
      notificaValutazione(valutate, prima)
    }
  } catch (e) { mieErrore.value = messaggioErrore(e, 'caricare le tue segnalazioni') }
  mieCaricamento.value = false
}

// cambio di stato visto dal polling: toast (o riquadro del nuovo livello) e punti aggiornati
async function notificaValutazione(valutate: Segnalazione[], prima: Map<number, Segnalazione>) {
  if (!utente.value) return
  if (scheda.value !== 'segnalazioni') mieNovita.value = true
  const s = valutate[0]!
  const punti = valutate.reduce((t, x) => t + (x.punti_ottenuti ?? 0) - (prima.get(x.id)?.punti_ottenuti ?? 0), 0)
  const chi = valutate.length > 1 ? `${valutate.length} tue segnalazioni` : `La tua segnalazione #${s.id}`
  const confermata = s.stato === 'confermata'
  if (punti > 0) {
    try {
      const d = await chiama<Utente>(`/utenti/${utente.value.id}`)
      applicaEsito({ punti_ottenuti: punti, punti: d.punti, livello: d.livello! }, `${chi} ${valutate.length > 1 ? 'sono state valutate' : 'è stata confermata'}`)
      return
    } catch {}
  }
  mostraToast({ nota: chi, testo: valutate.length > 1 ? 'Sono state valutate' : confermata ? 'È stata confermata' : 'Archiviata come falso allarme', esito: confermata ? 'ok' : 'no' }, 4000)
}

function mostraToast(t: { testo: string; nota?: string; esito?: 'ok' | 'no' }, durata = 2500) {
  toast.value = { id: Date.now(), ...t }
  clearTimeout(tToast); tToast = setTimeout(() => (toast.value = null), durata)
}

let chiaveAloni = ''
// un solo requestAnimationFrame per gli aloni presenti: hotspot (se ce ne sono) e proprie segnalazioni in valutazione
function aggiornaAloni() {
  const m = mappa
  if (!m) return
  const lista: Alone[] = []
  if (datiHotspot.features?.length) lista.push(ALONE_HOTSPOT)
  if (mie.value.some((s) => s.stato === 'nuova')) lista.push(aloneSegnalazioni('mie'))
  const k = lista.map((a) => a.layer).join()
  if (k === chiaveAloni) return
  chiaveAloni = k; fermaAloni()
  fermaAloni = lista.length ? animaAloni(m, lista) : () => {}
}

function aggiornaPinMie() {
  (mappa?.getSource('mie') as maplibregl.GeoJSONSource | undefined)?.setData(geojsonSegnalazioni(mie.value))
  aggiornaAloni()
}

function apriPopupMia(s: Segnalazione) {
  if (!mappa) return
  popupMia?.remove(); popupMiaId = s.id
  popupMia = apriPopup(mappa, [s.lon, s.lat], PopupSegnalazione, { s })
}

// dall'elenco: torna alla mappa, vola sul pin e apre il popup
async function mostraSuMappa(s: Segnalazione) {
  if (pannello.value) await chiudi()
  scheda.value = 'mappa'
  await nextTick()
  const m = mappa
  if (!m) return
  m.resize()
  m.flyTo({ center: [s.lon, s.lat], zoom: Math.max(m.getZoom(), 13), duration: 900 })
  m.once('moveend', () => apriPopupMia(s))
}

function caricaHotspot() {
  chiama<any>('/hotspot').then((g) => {
    datiHotspot = g; (mappa?.getSource('hotspot') as maplibregl.GeoJSONSource | undefined)?.setData(g)
    // gli aloni si animano solo se ci sono pin: niente ridisegno continuo della mappa a vuoto
    aggiornaAloni()
  }).catch(() => {})
}

function caricaRischio() {
  rischio.value = null; rischioErrore.value = false
  chiama<Rischio>(`/rischio?lat=${centro.value[1]}&lon=${centro.value[0]}`).then((r) => (rischio.value = r)).catch(() => (rischioErrore.value = true))
}

function cambiaUtente() {
  fermaAloni(); mappa?.remove(); mappa = null; marcatore = null; datiHotspot = VUOTO; chiaveAloni = ''
  clearInterval(tMie); note = null; mie.value = []; mieCaricamento.value = true; mieNovita.value = false; popupMia = null
  utente.value = null; pannello.value = false; esito.value = null; missione.value = null; scheda.value = 'mappa'
  try { localStorage.removeItem('utenteId') } catch {}
}

const VUOTO = { type: 'FeatureCollection' as const, features: [] }
let datiHotspot: any = VUOTO

function avviaMappa() {
  if (!contenitore.value) return
  registraPmtiles()
  mappa = new maplibregl.Map({
    container: contenitore.value, style: stileMappa(tema.value), center: centro.value, zoom: 12,
    attributionControl: false, locale: LOCALE_MAPPA,
  })
  limitaMappa(mappa)
  mappaPronta.value = mappa
  // sorgenti e layer si (ri)aggiungono a ogni stile caricato: anche dopo il cambio tema
  mappa.on('style.load', aggiungiLivelli)
  // Gestori registrati subito, non su 'load': i clic per livello valgono anche prima che il
  // livello esista, e 'load' puo' non arrivare mai se una risorsa della mappa fallisce.
  {
    const m = mappa
    clicIncendio(m, ['mie', 'hotspot'], () => pannello.value || !!missione.value)
    clicHotspot(m, ['mie'], () => pannello.value || !!missione.value)
    m.on('click', 'mie', (ev) => {
      if (pannello.value || missione.value) return
      const s = mie.value.find((x) => x.id === ev.features?.[0]?.properties?.id)
      if (s) apriPopupMia(s)
    })
    m.on('mouseenter', 'mie', () => (m.getCanvas().style.cursor = 'pointer'))
    m.on('mouseleave', 'mie', () => (m.getCanvas().style.cursor = ''))
    m.on('click', (ev) => {
      if (!pannello.value && !missione.value) return
      impostaPos(ev.lngLat.lat, ev.lngLat.lng)
    })
    caricaHotspot()
  }
}

function aggiungiLivelli() {
  const m = mappa
  if (!m || m.getSource('storico')) return
  const c = coloriMappa(tema.value)
  aggiungiStoricoIncendi(m, c, filtro.value)
  aggiungiHotspot(m, c, datiHotspot)
  // proprie segnalazioni sopra storico e hotspot: in valutazione ambra con onda, confermate macchia, falsi allarmi ad anello
  aggiungiPinSegnalazioni(m, 'mie', c, geojsonSegnalazioni(mie.value), { nuova: c.ambra, confermata: c.macchia })
}

watch(tema, (t) => mappa?.setStyle(stileMappa(t), { diff: false }))

// filtro anni istantaneo: i dati sono gia' nei tile
watch(filtro, (f) => impostaStoricoIncendi(mappa, f))

// punto scelto: pin pulsante (`.pin` in tema.css) del colore del significato:
// fuoco brace, area a rischio ambra, missione di mappatura macchia
function coloraPin() {
  const c = marcatore?.getElement().classList
  c?.add('pin')
  c?.toggle('pin-macchia', !!missione.value)
  c?.toggle('pin-ambra', !missione.value && tipo.value === 'area_a_rischio')
}
watch([tipo, missione], coloraPin)

function impostaPos(lat: number, lon: number) {
  pos.value = { lat, lon }
  if (!mappa) return
  if (!marcatore) marcatore = new maplibregl.Marker({ element: document.createElement('div'), anchor: 'center' })
  coloraPin()
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
function applicaEsito(r: { punti_ottenuti: number; punti: number; livello: Livello }, nota?: string) {
  if (!utente.value) return
  const vecchio = utente.value.livello?.nome
  utente.value = { ...utente.value, punti: r.punti, livello: r.livello }
  // salto di livello: il riquadro grande porta anche i punti, niente toast sovrapposto
  if (vecchio && vecchio !== r.livello.nome) {
    toast.value = null
    nuovoLivello.value = { nome: r.livello.nome, punti: r.punti_ottenuti }
    clearTimeout(tLivello); tLivello = setTimeout(() => (nuovoLivello.value = null), 3600)
  } else if (r.punti_ottenuti > 0) {
    mostraToast({ testo: `+${r.punti_ottenuti} punti`, nota }, nota ? 4000 : 2500)
  }
}

watch(scheda, async (s) => {
  if (s === 'segnalazioni') mieNovita.value = false
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
    errore.value = String(e.message).startsWith('409') ? 'Hai raggiunto il limite di oggi per questa missione.' : messaggioErrore(e, 'inviare la missione')
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
    caricaMie()
    if (esito.value.punti_ottenuti > 0) {
      const d = await chiama<Utente>(`/utenti/${utente.value.id}`)
      applicaEsito({ punti_ottenuti: esito.value.punti_ottenuti, punti: d.punti, livello: d.livello! })
    }
  } catch (e) { errore.value = messaggioErrore(e, 'inviare la segnalazione') }
  inCorso.value = false
}
</script>

<template>
  <main class="relative h-dvh overflow-hidden">
    <!-- scelta utente: schermata d'ingresso -->
    <section v-if="!utente" class="mx-auto flex h-dvh max-w-md flex-col overflow-y-auto px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-8">
      <div class="flex items-center justify-between">
        <NuxtLink to="/" class="pillola flex size-10 items-center justify-center" aria-label="Torna all'inizio"><ArrowLeft class="size-4 text-testo-2" /></NuxtLink>
        <InterruttoreTema />
      </div>

      <div class="mt-10 flex flex-col items-center text-center">
        <span class="flex size-12 items-center justify-center rounded-[32%] bg-gradient-to-b from-[#f2581d] to-[#d33515] shadow-[0_6px_18px_-8px_rgba(255,90,31,.6),inset_0_1px_0_rgba(255,255,255,.2)]">
          <Flame class="size-6 text-white" aria-hidden="true" />
        </span>
        <h1 class="mt-4 font-[family-name:var(--font-display)] text-[1.75rem] font-semibold tracking-tight">Sentinelle</h1>
        <p class="mt-1 max-w-[18rem] text-[.9rem] text-testo-2">Occhi accesi sulla Sardegna. Segnala, previeni, proteggi il tuo comune.</p>
      </div>

      <p class="etichetta mt-8 mb-2 px-1">Chi sei?</p>
      <StatoErrore v-if="erroreUtenti" :messaggio="erroreUtenti" @riprova="caricaUtenti" />
      <ul v-else-if="caricamentoUtenti" class="vetro divide-y divide-bordo overflow-hidden !p-0" aria-busy="true" aria-label="Caricamento delle sentinelle">
        <li v-for="k in 5" :key="k" class="flex items-center gap-3 px-4 py-3">
          <span class="scheletro size-10 shrink-0 !rounded-full" />
          <span class="flex-1 space-y-1.5"><span class="scheletro block h-3.5 w-28" /><span class="scheletro block h-2.5 w-16" /></span>
          <span class="scheletro h-3.5 w-9" />
        </li>
      </ul>
      <p v-else-if="!utenti.length" class="vetro p-6 text-center text-sm text-testo-2">Nessuna sentinella registrata.</p>
      <ul v-else class="vetro divide-y divide-bordo overflow-hidden !p-0">
        <li v-for="u in utenti" :key="u.id">
          <button class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-vetro-forte active:bg-vetro-forte" @click="scegli(u)">
            <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-vetro-forte text-[.74rem] font-semibold ring-1 ring-bordo-luce">{{ iniziali(u.nome) }}</span>
            <span class="min-w-0 flex-1 leading-tight">
              <span class="block truncate font-semibold">{{ u.nome }}</span>
              <span class="block text-[.76rem] text-testo-2">{{ nomeComune(u.comune) }}</span>
            </span>
            <span class="cifre flex items-center gap-1 text-[.86rem] font-medium text-testo-2"><Star class="size-3.5 fill-ambra text-ambra" aria-hidden="true" />{{ u.punti }}</span>
            <ChevronRight class="size-4 text-testo-3" aria-hidden="true" />
          </button>
        </li>
      </ul>
    </section>

    <template v-else>
      <!-- la mappa sta sotto tutto, sempre -->
      <div class="mappa-app absolute inset-0"><div ref="contenitore" class="h-full w-full" /></div>

      <!-- header: pillole fluttuanti -->
      <header class="pointer-events-none absolute inset-x-0 top-0 z-20 px-3 pt-[max(.75rem,env(safe-area-inset-top))]">
        <div class="flex items-start gap-2">
          <!-- larghezza intrinseca: la pillola segue il contenuto, non la finestra -->
          <button type="button" class="pillola pointer-events-auto flex h-11 max-w-[min(18rem,calc(100vw-9.5rem))] min-w-0 items-center pr-3 pl-1 text-left transition-colors hover:bg-vetro-forte" aria-label="Il tuo profilo: tocca per cambiare utente" @click="cambiaUtente">
            <IndicatoreLivello :nome="utente.nome" :punti="utente.punti" :livello="utente.livello" />
          </button>
          <span class="flex-1" />
          <IndicatoreRischio class="pointer-events-auto" :rischio="rischio" :errore="rischioErrore" @riprova="caricaRischio" />
          <InterruttoreTema compatto class="pointer-events-auto" />
        </div>
      </header>

      <!-- colonna destra sotto il tema: Livelli, zoom, "i" (passo 14 px dal flex; il posto di Livelli resta anche se nascosto) -->
      <div class="absolute top-[calc(max(.75rem,env(safe-area-inset-top))+58px)] right-3 z-20 flex w-11 flex-col items-center gap-[14px]">
        <div class="size-11"><PulsanteLivelli v-if="scheda === 'mappa' && !missione" v-model="filtro" :filtri="FILTRI" class="relative" /></div>
        <ControlliMappa :mappa="mappaPronta" />
      </div>

      <!-- missione `posizione`: scegli il punto -->
      <Transition name="foglio">
        <section v-if="scheda === 'mappa' && missione" class="sospeso fixed inset-x-2 bottom-[5.25rem] z-20 mx-auto max-w-[440px] space-y-3 p-3">
          <div>
            <p class="etichetta">Missione · +{{ missione.punti }} punti</p>
            <p class="mt-0.5 text-base font-semibold">{{ missione.titolo }}</p>
          </div>
          <p class="flex items-center gap-2 rounded-m border p-3 text-sm" :class="pos ? 'border-macchia/40 bg-macchia/10 font-semibold text-macchia' : 'border-bordo bg-vetro text-testo-2'">
            <MapPin class="size-4 shrink-0" aria-hidden="true" />
            <span class="cifre">{{ pos ? `Punto scelto: ${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}` : 'Tocca la mappa per indicare il punto' }}</span>
          </p>
          <div class="grid grid-cols-2 gap-2">
            <button type="button" class="secondario flex h-10 items-center justify-center gap-1.5 text-sm" @click="usaGps"><LocateFixed class="size-4" aria-hidden="true" /> Usa GPS</button>
            <label class="secondario flex h-10 items-center justify-center gap-1.5 border-dashed px-3 text-sm">
              <Camera class="size-4 shrink-0 text-testo-2" aria-hidden="true" /><span class="truncate">{{ foto ? foto.name : 'Foto' }}</span>
              <input type="file" accept="image/*" capture="environment" class="sr-only" @change="foto = ($event.target as HTMLInputElement).files?.[0] ?? null" />
            </label>
          </div>
          <p v-if="errore" class="text-sm text-brace" role="alert">{{ errore }}</p>
          <div class="grid grid-cols-[auto_1fr] gap-2">
            <button type="button" class="secondario h-11 px-5 text-sm" @click="annullaMissione">Annulla</button>
            <button type="button" class="primario h-11 text-sm" :disabled="!pos || inCorso" @click="confermaMissione">{{ inCorso ? 'Invio…' : `Conferma · +${missione.punti}` }}</button>
          </div>
        </section>
      </Transition>

      <!-- l'unico accento pieno -->
      <Transition name="foglio">
        <button v-if="scheda === 'mappa' && !pannello && !missione" type="button" class="primario fixed bottom-[5.5rem] left-1/2 z-20 flex h-12 w-[min(16rem,calc(100%-2.5rem))] -translate-x-1/2 items-center justify-center gap-2 text-[.98rem]" @click="apri">
          <Flame class="size-5" aria-hidden="true" /> Segnala
        </button>
      </Transition>

      <!-- segnalazione ed esito -->
      <Transition name="foglio">
        <section v-if="scheda === 'mappa' && pannello && !missione" class="sospeso fixed inset-x-2 bottom-[5.25rem] z-20 mx-auto max-h-[calc(100dvh-11rem)] max-w-[440px] overflow-y-auto p-3" aria-labelledby="titolo-pannello">
          <!-- esito: intestazione compatta -->
          <div v-if="esito" class="mb-4 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="flex items-center gap-1.5 text-[.74rem] font-medium text-macchia">
                <CircleCheck class="size-3.5" aria-hidden="true" /> Inviata · in coda agli operatori
              </p>
              <h2 id="titolo-pannello" class="mt-1 text-base font-semibold">{{ esito.tipo === 'fuoco' ? 'Fuoco o fumo' : 'Area a rischio' }}</h2>
              <p class="cifre mt-0.5 truncate text-[.76rem] text-testo-2">
                #{{ esito.id }} · {{ oraBreve(esito.creata_il) }}<template v-if="esito.comune"> · {{ nomeComune(esito.comune) }}</template> · {{ esito.lat.toFixed(4) }}, {{ esito.lon.toFixed(4) }}
              </p>
            </div>
            <button type="button" aria-label="Chiudi" class="secondario tocco flex size-8 shrink-0 items-center justify-center" @click="chiudi"><X class="size-4" /></button>
          </div>
          <div v-else class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="etichetta">Nuova segnalazione</p>
              <h2 id="titolo-pannello" class="mt-0.5 text-base font-semibold">Cosa vedi?</h2>
            </div>
            <button type="button" aria-label="Chiudi" class="secondario tocco flex size-8 shrink-0 items-center justify-center" @click="chiudi"><X class="size-4" /></button>
          </div>

          <!-- esito -->
          <div v-if="esito" class="space-y-4">
            <ScomposizionePriorita :priorita="esito.priorita" :fattori="esito.fattori" :motivazioni="esito.motivazioni" />
            <div class="flex items-center gap-3">
              <p v-if="(esito.punti_ottenuti ?? 0) > 0" class="cifre flex items-center gap-1 text-[.8rem] font-semibold text-ambra"><Star class="size-3.5 fill-current" aria-hidden="true" /> +{{ esito.punti_ottenuti }} punti</p>
              <button type="button" class="secondario ml-auto h-9 px-5 text-sm" @click="chiudi">Fatto</button>
            </div>
          </div>

          <!-- modulo -->
          <form v-else class="space-y-3" @submit.prevent="invia">
            <div class="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Tipo di segnalazione">
              <button type="button" role="radio" :aria-checked="tipo === 'fuoco'" class="flex flex-col items-start gap-1.5 rounded-m border p-3 text-left transition-colors" :class="tipo === 'fuoco' ? 'border-brace/60 bg-brace/12 ' : 'border-bordo bg-vetro hover:bg-vetro-forte'" @click="tipo = 'fuoco'">
                <Flame class="size-5" :class="tipo === 'fuoco' ? 'text-brace' : 'text-testo-3'" aria-hidden="true" />
                <span class="text-[.88rem] font-semibold leading-tight">Fuoco o fumo</span>
                <span class="text-[.72rem] text-testo-2">Lo vedi adesso</span>
              </button>
              <button type="button" role="radio" :aria-checked="tipo === 'area_a_rischio'" class="flex flex-col items-start gap-1.5 rounded-m border p-3 text-left transition-colors" :class="tipo === 'area_a_rischio' ? 'border-ambra/60 bg-ambra/12 ' : 'border-bordo bg-vetro hover:bg-vetro-forte'" @click="tipo = 'area_a_rischio'">
                <TriangleAlert class="size-5" :class="tipo === 'area_a_rischio' ? 'text-ambra' : 'text-testo-3'" aria-hidden="true" />
                <span class="text-[.88rem] font-semibold leading-tight">Area a rischio</span>
                <span class="text-[.72rem] text-testo-2">Sterpaglie, rifiuti…</span>
              </button>
            </div>

            <div class="flex items-center gap-2 rounded-full border p-1.5 pl-4" :class="pos ? 'border-macchia/40 bg-macchia/10' : 'border-bordo bg-vetro'">
              <MapPin class="size-4 shrink-0" :class="pos ? 'text-macchia' : 'text-testo-3'" aria-hidden="true" />
              <span class="cifre min-w-0 flex-1 text-[.82rem] leading-tight" :class="pos ? 'font-semibold text-macchia' : 'text-testo-2'">
                {{ pos ? `${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}` : 'Tocca la mappa per indicare il punto' }}
              </span>
              <button type="button" class="secondario tocco flex h-9 shrink-0 items-center gap-1.5 px-3 text-[.8rem]" @click="usaGps"><LocateFixed class="size-4" aria-hidden="true" /> GPS</button>
            </div>

            <label class="flex items-center gap-3 rounded-m border border-dashed border-bordo-luce bg-vetro p-3 text-sm">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-s bg-vetro-forte"><Camera class="size-4 text-testo-2" aria-hidden="true" /></span>
              <span class="min-w-0 leading-tight">
                <span class="block truncate font-semibold">{{ foto ? foto.name : 'Aggiungi una foto' }}</span>
                <span class="block text-[.72rem] text-testo-2">{{ foto ? 'Tocca per cambiarla' : 'Facoltativa, aiuta gli operatori' }}</span>
              </span>
              <input type="file" accept="image/*" capture="environment" class="sr-only" @change="foto = ($event.target as HTMLInputElement).files?.[0] ?? null" />
            </label>

            <p v-if="errore" class="text-sm text-brace" role="alert">{{ errore }}</p>
            <button class="primario flex h-12 w-full items-center justify-center gap-2 text-[.95rem]" :disabled="!pos || inCorso">
              <Loader2 v-if="inCorso" class="size-4 animate-spin" aria-hidden="true" />{{ inCorso ? 'Invio…' : 'Invia segnalazione' }}
            </button>
          </form>
        </section>
      </Transition>

      <!-- missioni e classifica: fogli sopra la mappa -->
      <Transition name="foglio">
        <section v-if="scheda === 'missioni'" class="sospeso fixed inset-x-2 top-[calc(max(.75rem,env(safe-area-inset-top))+3.5rem)] bottom-[5.25rem] z-20 mx-auto max-w-[480px] overflow-y-auto sm:bottom-auto sm:max-h-[calc(100dvh-9.75rem)]">
          <SchedaMissioni :utente="utente" @esito="applicaEsito" @posizione="scegliPunto" />
        </section>
      </Transition>
      <Transition name="foglio">
        <section v-if="scheda === 'classifica'" class="sospeso fixed inset-x-2 top-[calc(max(.75rem,env(safe-area-inset-top))+3.5rem)] bottom-[5.25rem] z-20 mx-auto max-w-[480px] overflow-y-auto sm:bottom-auto sm:max-h-[calc(100dvh-9.75rem)]">
          <SchedaClassifica :comune="utente.comune" :nome-utente="utente.nome" />
        </section>
      </Transition>

      <Transition name="foglio">
        <section v-if="scheda === 'segnalazioni'" class="sospeso fixed inset-x-2 top-[calc(max(.75rem,env(safe-area-inset-top))+3.5rem)] bottom-[5.25rem] z-20 mx-auto max-w-[480px] overflow-y-auto sm:bottom-auto sm:max-h-[calc(100dvh-9.75rem)]">
          <SchedaSegnalazioni :elenco="mie" :caricamento="mieCaricamento" :errore="mieErrore" @apri="mostraSuMappa" @riprova="caricaMie" />
        </section>
      </Transition>

      <BarraNavigazione v-model="scheda" :avviso="mieNovita" />
      <ToastPunti :toast="toast" :nuovo-livello="nuovoLivello" @chiudi-livello="nuovoLivello = null" />
    </template>
  </main>
</template>

<style>
/* fogli: salgono con easing in uscita, se ne vanno piu' in fretta (niente sovrapposizioni lunghe) */
.foglio-enter-active { transition: opacity .2s ease-out, transform .32s cubic-bezier(.22, 1, .36, 1); }
.foglio-leave-active { transition: opacity .14s ease-in, transform .14s ease-in; }
.foglio-enter-from { opacity: 0; transform: translateY(28px); }
.foglio-leave-to { opacity: 0; transform: translateY(10px); }
</style>
