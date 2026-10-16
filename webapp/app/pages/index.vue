<script setup lang="ts">
// Mappa: dove sono, verso dove guardo, cosa succede vicino a me. In cima la barra dei pericoli; in basso SEGNALA e Chiama.
import type { Map as MappaLibre, Marker } from 'maplibre-gl'
import { Bell, Camera, LocateFixed, MapPin, Navigation2, Phone } from '@lucide/vue'

const api = useApi()
const { id } = useSessione()
const { pos, reale, stato: statoPos, avvia: avviaPos } = usePosizione()
const bussola = useBussola()
const avvisi = useAvvisi()
const bozza = useBozza()
const eventi = useEventi()
const toast = useToast()
const route = useRoute()
const { vista, imposta: impostaVistaScelta } = useVistaMappa()

const mappa = shallowRef<MappaLibre>()
const io = shallowRef<MarcatoreIo>()
const segui = ref(true)
const orientata = ref(false) // mappa girata come guardo (altrimenti nord in alto)
const rotazione = ref(0)
const condivise = ref<Condivisa[]>([])
const scelta = ref<Condivisa | null>(null)
const gruppo = ref<Condivisa[] | null>(null)
const apertoAvvisi = ref(false)
const apertoChiama = ref(false)
const luogo = ref('')
const voto = ref(false)
const caricate = ref(false) // segnalazioni lette almeno una volta con la posizione gia' nota
let inquadrata = false
let pin: Marker[] = []
let ultimaRicerca = { lat: 0, lon: 0 }
let rf = 0

// punto da una segnalazione dello storico (?punto=lat,lon&seg=id)
const daStorico = (() => {
  const [lat, lon] = String(route.query.punto ?? '').split(',').map(Number)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { lat: lat!, lon: lon!, seg: Number(route.query.seg) || null } : null
})()
if (daStorico) segui.value = false

const centroIniziale: [number, number] = daStorico ? [daStorico.lon, daStorico.lat] : [pos.value.lon, pos.value.lat]
// spazio coperto dai controlli sulla mappa: barra dei pericoli e pillole in alto, torna-a-me in basso
const MARGINE = { top: 150, bottom: 64, left: 28, right: 28 }

// --- barra dei pericoli --------------------------------------------------------------------------------
const vicine = computed(() => condivise.value
  .filter((c) => c.stato_ufficiale !== 'spento' && c.tipo !== 'area_a_rischio')
  .map((c) => ({ ...c, d: metri(pos.value, c) }))
  .filter((c) => c.d <= 5000)
  .sort((a, b) => a.d - b.d))

const verso = (da: { lat: number; lon: number }, a: { lat: number; lon: number }) => puntoCardinale(direzioneVerso(da, a))

const banner = computed(() => {
  // 1) avvisi sui miei luoghi (urgenti o importanti), 2) segnalazioni entro 5 km da dove sono, 3) tutto tranquillo
  const a = avvisi.lista.value.find((x) => x.priorita !== 'informazione' && x.tipo !== 'rischio')
  if (a && a.tipo !== 'rischio') {
    const vicino = a.distanza_km != null && a.distanza_km < 0.15
    return {
      tono: a.priorita === 'urgente' ? 'pericolo' as const : 'attenzione' as const, tipo: a.tipo,
      titolo: vicino ? `${TIPI[a.tipo].nome} vicino a ${a.localita_nome}` : `${TIPI[a.tipo].nome} a ${km(a.distanza_km)}`,
      sotto: [vicino ? '' : `da ${a.localita_nome}, verso ${verso({ lat: a.da_lat, lon: a.da_lon }, a)}`, fa(a.creato_il)].filter(Boolean).join(' · '),
      altri: avvisi.lista.value.filter((x) => x.priorita !== 'informazione').length - 1,
      punto: { lat: a.lat, lon: a.lon, tipo: a.tipo },
    }
  }
  const v = vicine.value[0]
  if (v) {
    return {
      tono: v.tipo === 'fuoco' && v.d < 2000 ? 'pericolo' as const : 'attenzione' as const, tipo: v.tipo,
      titolo: `${TIPI[v.tipo].nome} a ${distanzaTesto(v.d)}`,
      sotto: `da te, verso ${verso(pos.value, v)} · ${fa(v.creata_il)}`, altri: vicine.value.length - 1,
      punto: { lat: v.lat, lon: v.lon, tipo: v.tipo },
    }
  }
  return { tono: 'tranquillo' as const, tipo: null, titolo: 'Tutto tranquillo', sotto: 'Nessun pericolo segnalato vicino a te', altri: 0, punto: null }
})

// --- mappa ---------------------------------------------------------------------------------------------
function pianifica() {
  if (rf) return
  rf = requestAnimationFrame(() => {
    rf = 0
    const m = mappa.value
    if (!m) return
    io.value?.aggiorna(pos.value, bussola.dir.value)
    // la rotazione col sensore non deve spezzare un movimento in corso (es. "torna a me")
    if (orientata.value && bussola.dir.value !== null && !m.isEasing()) m.setBearing(bussola.dir.value)
  })
}

function pronta(m: MappaLibre) {
  mappa.value = m
  preparaPosizione(m)
  io.value = creaMarcatoreIo(m)
  pianifica()
  m.on('dragstart', () => (segui.value = false))
  m.on('rotate', () => (rotazione.value = m.getBearing()))
  m.on('zoomend', disegnaPin) // i gruppi dipendono dallo zoom
  caricaCondivise()
}

// Vista iniziale: il cerchio dell'incidente a cui si riferisce la barra dei pericoli entra per intero nello schermo,
// insieme a me se e' entro 6 km. Da una segnalazione dello storico: il suo cerchio. Senza incidenti: io, zoom 16.
function inquadraIniziale() {
  const m = mappa.value
  if (!m || inquadrata || !caricate.value) return
  inquadrata = true
  const bersaglio = daStorico
    ? { lat: daStorico.lat, lon: daStorico.lon, tipo: condivise.value.find((c) => c.id === daStorico.seg)?.tipo }
    : banner.value.punto
  if (!bersaglio) return
  // anche i cerchi delle altre segnalazioni nello stesso punto (fuoco, fumo e terreno insieme) devono starci
  const cerchi = [bersaglio, ...condivise.value.filter((c) => c.stato_ufficiale !== 'spento' && metri(c, bersaglio) < 150)]
  const vicino = !daStorico && metri(pos.value, bersaglio) <= 6000
  const cam = cameraCerchi(m, cerchi, MARGINE, vicino ? pos.value : undefined)
  if (!cam) return
  segui.value = false // l'inquadratura non e' centrata su di me: "torna a me" riprende a seguirmi
  m.jumpTo({ center: cam.center, zoom: cam.zoom })
}

function disegnaPin() {
  const m = mappa.value
  if (!m) return
  pin.forEach((p) => p.remove())
  impostaIncidenti(m, condivise.value)
  pin = raggruppa(m, condivise.value).map((g) => {
    const c = g.principale
    return mettiPin(m, c.lat, c.lon, {
      icona: c.tipo, conteggio: g.membri.length, onda: c.tipo === 'fuoco' && c.stato_ufficiale !== 'spento',
      classe: [c.mia ? 'pin-mia' : '', c.id === daStorico?.seg ? 'pin-selezionato' : '', c.stato_ufficiale === 'spento' ? 'opacity-70' : ''].join(' '),
      nome: g.membri.length > 1 ? `${g.membri.length} segnalazioni, la più grave: ${TIPI[c.tipo].nome}` : `${TIPI[c.tipo].nome}, segnalato ${fa(c.creata_il)}`,
      alTocco: () => tocca(g.membri),
    })
  })
}

function tocca(membri: Condivisa[]) {
  if (membri.length === 1) { scelta.value = membri[0]!; return }
  const m = mappa.value
  const stessoPunto = membri.every((c) => metri(c, membri[0]!) < 15)
  if (!m || stessoPunto || m.getZoom() >= 17.5) { gruppo.value = membri; return }
  segui.value = false
  inquadra(m, membri, { margine: 90, zoomMax: 17.5 }) // avvicinandosi il gruppo si scioglie
}

async function caricaCondivise() {
  try {
    const d = 0.35
    const bbox = [pos.value.lon - d, pos.value.lat - d * 0.8, pos.value.lon + d, pos.value.lat + d * 0.8].join(',')
    condivise.value = await api<Condivisa[]>('/segnalazioni/attive', { query: { bbox, utente_id: id.value } })
    disegnaPin()
    if (scelta.value) scelta.value = condivise.value.find((c) => c.id === scelta.value!.id) ?? null
  } catch { /* si tengono i pin di prima */ }
  if (statoPos.value !== 'attesa') { caricate.value = true; inquadraIniziale() }
}

function vaiAMe() {
  segui.value = true
  const m = mappa.value
  if (!m) return
  m.flyTo({
    center: [pos.value.lon, pos.value.lat], zoom: Math.max(m.getZoom(), 16), duration: 700, essential: true,
    bearing: orientata.value && bussola.dir.value !== null ? bussola.dir.value : m.getBearing(),
  })
}

function vaiA(lat: number, lon: number) {
  segui.value = false
  apertoAvvisi.value = false
  mappa.value?.flyTo({ center: [lon, lat], zoom: 15.5, duration: 800 })
}

// bussola: se la mappa e' girata (o in modo "come guardo") riporta il nord in alto; altrimenti gira come guardo
function alternaOrientamento() {
  const m = mappa.value
  if (!m) return
  if (orientata.value || Math.abs(m.getBearing()) > 1) {
    orientata.value = false
    m.easeTo({ bearing: 0, duration: 400 })
    return
  }
  if (bussola.dir.value === null) { toast.errore('La bussola non è disponibile su questo dispositivo.'); return }
  orientata.value = true
  m.easeTo({ bearing: bussola.dir.value, duration: 400 })
}

watch(pos, () => {
  pianifica()
  if (segui.value) mappa.value?.easeTo({ center: [pos.value.lon, pos.value.lat], duration: 600 })
  cercaLuogo()
})
watch(() => bussola.dir.value, pianifica)
// col primo punto GPS (o il rifiuto) le segnalazioni si rileggono attorno a dove sono davvero
watch(statoPos, (s) => { if (s !== 'attesa') caricaCondivise() })

async function cercaLuogo() {
  if (metri(pos.value, ultimaRicerca) < 60) return
  ultimaRicerca = { lat: pos.value.lat, lon: pos.value.lon }
  try {
    const l = await api<{ comune: string | null; indirizzo: string | null }>('/luogo', { query: { lat: pos.value.lat, lon: pos.value.lon } })
    luogo.value = l.indirizzo ?? l.comune ?? ''
  } catch { /* resta l'ultimo nome */ }
}

function satelliteKo() {
  impostaVistaScelta('mappa', false) // non si salva: alla prossima volta riprova col satellite
  toast.errore('Il satellite non è raggiungibile: mostro la mappa normale.')
}

// --- segnala ------------------------------------------------------------------------------------------
function dopoFoto(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  input.value = ''
  if (!f) return
  bozza.azzera()
  bozza.foto.value = f
  navigateTo('/segnala')
}

// --- voto su una segnalazione condivisa ----------------------------------------------------------------
async function vota(c: Condivisa, v: 'ancora' | 'finito') {
  voto.value = true
  try {
    const body = new FormData()
    body.append('utente_id', String(id.value))
    body.append('voto', v)
    body.append('lat', String(pos.value.lat))
    body.append('lon', String(pos.value.lon))
    await api(`/segnalazioni/${c.id}/voto`, { method: 'POST', body })
    toast.ok(v === 'ancora' ? 'Grazie, la tua conferma è stata registrata.' : 'Grazie, abbiamo segnato che non c’è più.')
    await caricaCondivise()
  } catch (e) {
    toast.errore(messaggioErrore(e))
  } finally {
    voto.value = false
  }
}

let disiscrivi: (() => void) | null = null
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  avviaPos()
  bussola.avvia()
  cercaLuogo()
  let r: ReturnType<typeof setTimeout>
  disiscrivi = eventi.on(['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata'], () => { clearTimeout(r); r = setTimeout(caricaCondivise, 500) })
  timer = setInterval(caricaCondivise, 60000)
})
onBeforeUnmount(() => {
  disiscrivi?.()
  if (timer) clearInterval(timer)
  cancelAnimationFrame(rf)
  pin.forEach((p) => p.remove())
  io.value?.rimuovi()
})
</script>

<template>
  <div class="schermata">
    <div class="relative min-h-0 flex-1">
      <MappaBase :centro="centroIniziale" :zoom="daStorico ? 15.5 : 16" :vista="vista" @pronta="pronta" @satellite-ko="satelliteKo" />

      <!-- in alto: barra dei pericoli, poi dove sono e che mappa vedo -->
      <div class="pointer-events-none absolute inset-x-3 top-3 flex flex-col gap-2">
        <div class="pointer-events-auto">
          <BannerPericolo :tono="banner.tono" :tipo="banner.tipo" :titolo="banner.titolo" :sotto="banner.sotto" :altri="banner.altri" @apri="apertoAvvisi = true" />
        </div>
        <div class="flex items-start justify-between gap-2">
          <span class="pillola pointer-events-auto min-h-10 min-w-0 text-base">
            <MapPin class="size-4 flex-none" aria-hidden="true" />
            <span class="truncate">{{ luogo || 'Sardegna' }}</span>
            <span v-if="!reale" class="etichetta e-ambra flex-none">prova</span>
          </span>
          <div class="segmenti pointer-events-auto flex-none !bg-white shadow-sollevato" role="group" aria-label="Vista della mappa">
            <button type="button" class="!min-h-9 !px-3 !text-sm" :aria-pressed="vista === 'satellite'" @click="impostaVistaScelta('satellite')">Satellite</button>
            <button type="button" class="!min-h-9 !px-3 !text-sm" :aria-pressed="vista === 'mappa'" @click="impostaVistaScelta('mappa')">Mappa</button>
          </div>
        </div>
        <div class="flex justify-end">
          <button type="button" class="tondo pointer-events-auto !size-12" :class="orientata ? '!bg-inchiostro !text-white' : ''" :aria-pressed="orientata" :aria-label="orientata || Math.abs(rotazione) > 1 ? 'Riporta il nord in alto' : 'Gira la mappa come guardi'" @click="alternaOrientamento">
            <Navigation2 :style="{ rotate: `${-rotazione}deg` }" class="transition-transform duration-150" aria-hidden="true" />
          </button>
        </div>
        <p v-if="statoPos === 'negata'" class="pillola pointer-events-auto !min-h-0 py-1.5 text-sm font-semibold">Consenti la posizione nelle impostazioni per vedere dove sei.</p>
      </div>

      <!-- in basso: verso dove guardo, torna a me -->
      <div class="pointer-events-none absolute inset-x-3 bottom-3 flex items-end justify-center">
        <button v-if="bussola.serveTocco.value" type="button" class="pillola pointer-events-auto min-h-10 text-base" @click="bussola.richiedi()">Attiva la bussola</button>
        <span v-else-if="bussola.stato.value === 'assente'" class="pillola !min-h-9 text-sm font-semibold tenue">Direzione non disponibile</span>
        <button type="button" class="tondo pointer-events-auto absolute bottom-0 right-0 !size-12" aria-label="Torna alla mia posizione" @click="vaiAMe"><LocateFixed aria-hidden="true" /></button>
      </div>
    </div>

    <!-- azioni: sempre in vista -->
    <div class="flex flex-none flex-col gap-1 border-t-[1.5px] border-linea bg-carta px-4 pb-1 pt-3">
      <div class="flex gap-3">
        <label class="gigante flex-1 cursor-pointer !min-h-[5.25rem]">
          <Camera aria-hidden="true" />
          <span class="text-[1.7rem] uppercase tracking-wide">Segnala</span>
          <input type="file" accept="image/*" capture="environment" class="sr-only" @change="dopoFoto">
        </label>
        <button type="button" class="gigante gigante-bianco !w-[5.25rem] flex-none !px-0" aria-label="Chiama i soccorsi" @click="apertoChiama = true">
          <Phone aria-hidden="true" />
        </button>
      </div>
      <NuxtLink to="/segnala" class="mx-auto flex min-h-10 items-center px-3 text-sm font-bold underline underline-offset-4" @click="bozza.azzera()">Segnala senza foto</NuxtLink>
    </div>

    <!-- chiamata -->
    <Foglio v-model="apertoChiama" titolo="Chi vuoi chiamare?">
      <h2 class="titolo mb-4 text-2xl">Chi vuoi chiamare?</h2>
      <div class="flex flex-col gap-3">
        <a href="tel:1515" class="gigante gigante-bianco !justify-start !text-left !text-xl"><Phone aria-hidden="true" /><span class="flex flex-col"><span>Chiama il 1515</span><span class="text-base font-semibold tenue">Incendi e boschi (Corpo Forestale)</span></span></a>
        <a href="tel:112" class="gigante !justify-start !text-left !text-xl"><Phone aria-hidden="true" /><span class="flex flex-col"><span>Chiama il 112</span><span class="text-base font-semibold opacity-90">Persone in pericolo</span></span></a>
      </div>
    </Foglio>

    <!-- avvisi e segnalazioni vicine -->
    <Foglio v-model="apertoAvvisi" titolo="Avvisi e segnalazioni vicine">
      <h2 class="titolo mb-3 text-2xl">Vicino a te</h2>
      <section v-if="avvisi.lista.value.length" class="mb-4">
        <h3 class="sottotitolo mb-2 flex items-center gap-2"><Bell class="size-5" aria-hidden="true" />I tuoi avvisi</h3>
        <ul class="elenco">
          <li v-for="a in avvisi.lista.value" :key="a.id" class="riga items-start">
            <span class="etichetta mt-0.5" :class="PRIORITA[a.priorita].classe">{{ PRIORITA[a.priorita].nome }}</span>
            <span class="flex-1"><span class="block text-lg font-bold leading-tight">{{ a.titolo }}</span><span class="tenue block">{{ a.testo }}</span></span>
            <button type="button" class="pulsante pulsante-piccolo" @click="vaiA(a.lat, a.lon)">Vedi</button>
          </li>
        </ul>
      </section>
      <section v-if="vicine.length" class="mb-4">
        <h3 class="sottotitolo mb-2">Segnalazioni entro 5 km</h3>
        <ul class="elenco">
          <li v-for="c in vicine" :key="c.id" class="riga">
            <span class="tile-tipo" :class="`t-${c.tipo}`"><IconaTipo :tipo="c.tipo" aria-hidden="true" /></span>
            <span class="flex-1"><span class="block text-lg font-bold leading-tight">{{ TIPI[c.tipo].nome }} · {{ distanzaTesto(c.d) }}</span><span class="tenue block">Segnalato {{ fa(c.creata_il) }}</span></span>
            <button type="button" class="pulsante pulsante-piccolo" @click="vaiA(c.lat, c.lon)">Vedi</button>
          </li>
        </ul>
      </section>
      <p v-if="!avvisi.lista.value.length && !vicine.length" class="tenue mb-4 text-lg">Nessun avviso e nessuna segnalazione entro 5 km. Per ricevere gli avvisi sulla tua casa e sui tuoi terreni, impostali in Località.</p>
      <NuxtLink to="/localita" class="pulsante w-full" @click="apertoAvvisi = false">Imposta gli avvisi</NuxtLink>
    </Foglio>

    <!-- più segnalazioni nello stesso punto -->
    <Foglio :model-value="!!gruppo" titolo="Segnalazioni in questo punto" @update:model-value="gruppo = null">
      <template v-if="gruppo">
        <h2 class="titolo mb-3 text-2xl">{{ gruppo.length }} segnalazioni qui</h2>
        <ul class="elenco">
          <li v-for="c in gruppo" :key="c.id" class="riga">
            <span class="tile-tipo" :class="`t-${c.tipo}`"><IconaTipo :tipo="c.tipo" aria-hidden="true" /></span>
            <span class="flex-1"><span class="block text-lg font-bold leading-tight">{{ TIPI[c.tipo].nome }}</span><span class="tenue block">Segnalato {{ fa(c.creata_il) }} · {{ STATI_UFFICIALI[c.stato_ufficiale] }}</span></span>
            <button type="button" class="pulsante pulsante-piccolo" @click="scelta = c; gruppo = null">Apri</button>
          </li>
        </ul>
      </template>
    </Foglio>

    <!-- scheda di una segnalazione sulla mappa -->
    <Foglio :model-value="!!scelta" titolo="Segnalazione" @update:model-value="scelta = null">
      <template v-if="scelta">
        <div class="flex items-center gap-3">
          <span class="tile-tipo" :class="`t-${scelta.tipo}`"><IconaTipo :tipo="scelta.tipo" aria-hidden="true" /></span>
          <div class="flex-1">
            <h2 class="titolo text-2xl">{{ TIPI[scelta.tipo].nome }}</h2>
            <p class="tenue text-lg">Segnalato {{ fa(scelta.creata_il) }} · a {{ distanzaTesto(metri(pos, scelta)) }} da te</p>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <span class="etichetta" :class="scelta.stato_ufficiale === 'mezzi_sul_posto' ? 'e-macchia' : scelta.stato_ufficiale === 'spento' ? '' : 'e-cielo'">{{ STATI_UFFICIALI[scelta.stato_ufficiale] }}</span>
          <span class="etichetta">{{ plurale(scelta.conferme, 'conferma', 'conferme') }}</span>
          <span v-if="scelta.probabilmente_spento" class="etichetta e-ambra">Forse è spento</span>
        </div>
        <p v-if="scelta.mia" class="tenue mt-4 text-lg">È una tua segnalazione.</p>
        <p v-else-if="scelta.mio_voto" class="tenue mt-4 text-lg">Hai già risposto: grazie.</p>
        <div v-else class="mt-4 flex gap-3">
          <button type="button" class="pulsante pulsante-scuro flex-1" :disabled="voto" @click="vota(scelta, 'ancora')">Lo vedo anch’io</button>
          <button type="button" class="pulsante flex-1" :disabled="voto" @click="vota(scelta, 'finito')">Non c’è più</button>
        </div>
      </template>
    </Foglio>
  </div>
</template>
