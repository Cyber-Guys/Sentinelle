<script setup lang="ts">
// Le mie località: casa e terreni su una mappa, ognuno con il suo rischio di oggi e i suoi avvisi.
import type { Map as MappaLibre, Marker } from 'maplibre-gl'
import { Bell, BellOff, ChevronDown, ChevronUp, Layers, Minus, Plus, TriangleAlert } from '@lucide/vue'

const api = useApi()
const { id } = useSessione()
const avvisi = useAvvisi()
const eventi = useEventi()

const lista = ref<Localita[]>([])
const caricamento = ref<'caricamento' | 'ok' | 'errore'>('caricamento')
const selezionata = ref<number | null>(null)
const zoneVisibili = ref(true)
const mappa = shallowRef<MappaLibre>()
const regione = ref<HTMLElement>() // mappa a tutta altezza; il pannello ci sta sopra, quindi la mappa non si ridimensiona mai
const pannello = ref<HTMLElement>()
const pin = new Map<number, Marker>()
let primoGiro = true

const corrente = computed(() => lista.value.find((l) => l.id === selezionata.value))
const altezzaPannello = () => pannello.value?.offsetHeight ?? 0
const { stile, maniglia } = useAltezzaPannello({ min: 150, max: () => (regione.value?.clientHeight ?? 600) * 0.85, fine: () => nextTick(dopoPannello) })

async function carica() {
  try {
    lista.value = await api<Localita[]>(`/utenti/${id.value}/localita`)
    caricamento.value = 'ok'
    if (!lista.value.some((l) => l.id === selezionata.value)) selezionata.value = null
    await nextTick() // il pannello ha la sua altezza vera solo a elenco disegnato
    disegna()
  } catch {
    caricamento.value = 'errore'
  }
}

function disegna() {
  const m = mappa.value
  if (!m) return
  pin.forEach((p) => p.remove())
  pin.clear()
  for (const l of lista.value) {
    pin.set(l.id, mettiPin(m, l.lat, l.lon, {
      icona: l.tipo, classe: `pin-l-${l.stato.livello.split(' ')[0]}`, etichetta: l.nome,
      nome: `${l.nome}: ${LIVELLI[l.stato.livello].nome}`, alTocco: () => seleziona(l.id),
    }))
  }
  evidenzia()
  impostaZone(m, 'tutte', {
    type: 'FeatureCollection', features: lista.value.flatMap((l) => l.stato.zone.features),
  })
  mostraZone(m, 'tutte', zoneVisibili.value)
  if (primoGiro && lista.value.length) {
    primoGiro = false
    inquadra(m, lista.value, { margine: { top: 30, bottom: altezzaPannello() + 30, left: 70, right: 70 }, zoomMax: 12.5 })
  }
}

// la selezione cambia solo l'aspetto del pin: i pin non si ricreano e non si spostano
const evidenzia = () => pin.forEach((p, id) => p.getElement().classList.toggle('pin-selezionato', id === selezionata.value))

function pronta(m: MappaLibre) {
  mappa.value = m
  disegna()
}

// porta la localita' al centro della parte di mappa che il pannello lascia libera
function centra(zoom?: number) {
  const m = mappa.value, x = corrente.value
  if (!m || !x) return
  m.easeTo({ center: [x.lon, x.lat], zoom: zoom ?? m.getZoom(), offset: [0, -altezzaPannello() / 2], duration: 600 })
}

// a pannello regolato: la localita' scelta si muove solo se il pannello l'ha coperta
function dopoPannello() {
  const m = mappa.value, x = corrente.value
  if (!m || !x) return
  const y = m.project([x.lon, x.lat]).y
  if (y < 40 || y > (regione.value?.clientHeight ?? 0) - altezzaPannello() - 30) centra()
}

function seleziona(l: number) {
  selezionata.value = l
  evidenzia()
  nextTick(() => centra(12.5)) // il pannello si e' gia' allargato col dettaglio
}

function chiudiDettaglio() {
  selezionata.value = null
  evidenzia()
}

watch(zoneVisibili, (v) => mappa.value && mostraZone(mappa.value, 'tutte', v))

const fascia = (l: Localita) => l.stato.n_zone === 0
  ? { classe: 'bg-macchia-fondo text-macchia', testo: 'Nessuna zona a rischio vicino' }
  : { classe: l.stato.livello === 'medio' ? 'bg-ambra-fondo text-ambra-testo' : 'bg-brace-fondo text-brace', testo: `${plurale(l.stato.n_zone, 'zona', 'zone')} a rischio vicino` }
const nomiTipi = (l: Localita) => l.avvisi_tipi.map((t) => TIPI[t].breve)
const tuttiAvvisiDi = (l: Localita) => avvisi.lista.value.filter((a) => a.localita_id === l.id)
const avvisiDi = (l: Localita) => tuttiAvvisiDi(l).slice(0, 1)
const colore = (l: Localita) => (l.stato.livello === 'basso' ? 'tile-macchia' : l.stato.livello === 'medio' ? 'tile-ambra' : 'tile-brace')

let disiscrivi: (() => void) | null = null
onMounted(() => {
  carica()
  let r: ReturnType<typeof setTimeout>
  disiscrivi = eventi.on(['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata'], () => { clearTimeout(r); r = setTimeout(carica, 800) })
})
onBeforeUnmount(() => { disiscrivi?.(); pin.forEach((p) => p.remove()) })
</script>

<template>
  <div class="schermata">
    <header class="flex flex-none items-center gap-2 px-4 pb-1.5 pt-3">
      <h1 class="titolo flex-1 text-[1.6rem]">Le mie località</h1>
    </header>

    <!-- mappa a tutta altezza, con sopra il pannello delle localita' (altezza regolabile dalla maniglia) -->
    <div ref="regione" class="relative min-h-0 flex-1 overflow-hidden">
      <MappaBase :centro="[8.9, 39.45]" :zoom="9" @pronta="pronta" />
      <div class="absolute right-3 top-3 flex flex-col gap-2">
        <button type="button" class="tondo !size-12" :class="zoneVisibili ? '' : '!bg-vuoto'" :aria-pressed="zoneVisibili" aria-label="Mostra le zone a rischio" @click="zoneVisibili = !zoneVisibili"><Layers aria-hidden="true" /></button>
        <button type="button" class="tondo !size-12" aria-label="Ingrandisci" @click="mappa?.zoomIn()"><Plus aria-hidden="true" /></button>
        <button type="button" class="tondo !size-12" aria-label="Riduci" @click="mappa?.zoomOut()"><Minus aria-hidden="true" /></button>
      </div>

      <section ref="pannello" class="foglio absolute inset-x-0 bottom-0 z-10 flex max-h-[85%] flex-col px-4" :style="stile">
        <div class="maniglia-area" role="button" tabindex="0" aria-label="Regola l'altezza dell'elenco" v-bind="maniglia"><div class="maniglia" /></div>
        <div class="mb-1.5 flex items-center gap-2">
          <h2 class="sottotitolo flex-1 text-lg">Località salvate</h2>
          <span v-if="caricamento === 'ok'" class="etichetta">{{ plurale(lista.length, 'luogo', 'luoghi') }}</span>
        </div>

        <div class="scorri !flex-[1_1_auto] -mx-1 flex flex-col gap-1.5 px-1 pb-1.5">
          <template v-if="caricamento === 'caricamento'">
            <div v-for="n in 3" :key="n" class="scheletro h-[3.75rem]" />
          </template>
          <StatoErrore v-else-if="caricamento === 'errore'" @riprova="carica" />
          <StatoVuoto v-else-if="!lista.length">
            <template #icona><IconaTipo tipo="casa" class="size-8" /></template>
            <template #titolo>Nessuna località</template>
            Aggiungi la tua casa e i tuoi terreni: ti avvisiamo se c’è fumo o fuoco vicino.
            <template #azione><NuxtLink to="/localita/nuova?tipo=casa" class="gigante !min-h-[4.25rem] !text-xl">Aggiungi la tua casa</NuxtLink></template>
          </StatoVuoto>

          <template v-else>
          <article v-for="l in lista" :key="l.id" class="scheda !p-0" :class="l.id === selezionata ? '!border-inchiostro !border-2' : ''">
            <button type="button" class="flex min-h-[3.75rem] w-full items-center gap-3 px-3 py-1.5 text-left" :aria-expanded="l.id === selezionata" @click="l.id === selezionata ? chiudiDettaglio() : seleziona(l.id)">
              <span class="tile-tipo" :class="colore(l)"><IconaTipo :tipo="l.tipo" aria-hidden="true" /></span>
              <span class="min-w-0 flex-1">
                <span class="block text-xl font-extrabold leading-tight">{{ l.nome }}</span>
                <span class="tenue block truncate text-base">{{ l.indirizzo ?? TIPI_LOCALITA[l.tipo] }}</span>
              </span>
              <span v-if="l.id !== selezionata" class="etichetta" :class="LIVELLI[l.stato.livello].classe">{{ LIVELLI[l.stato.livello].nome }}</span>
              <component :is="l.id === selezionata ? ChevronUp : ChevronDown" class="size-6 flex-none" aria-hidden="true" />
            </button>

            <div v-if="l.id === selezionata" class="flex flex-col gap-2 px-3 pb-2.5">
              <div class="flex items-center gap-2 rounded-xl px-3 py-2 text-lg font-bold" :class="fascia(l).classe">
                <TriangleAlert class="size-5 flex-none" aria-hidden="true" />{{ fascia(l).testo }}
              </div>
              <div class="flex flex-wrap items-center gap-2 text-base">
                <template v-if="l.avvisi_attivi">
                  <Bell class="size-5" aria-hidden="true" /><span class="font-semibold">Avvisi attivi:</span>
                  <span v-for="n in nomiTipi(l)" :key="n" class="etichetta e-brace">{{ n }}</span>
                </template>
                <template v-else><BellOff class="size-5" aria-hidden="true" /><span class="font-semibold">Avvisi spenti</span></template>
              </div>
              <ul v-if="avvisiDi(l).length" class="flex flex-col gap-1.5">
                <li v-for="a in avvisiDi(l)" :key="a.id" class="flex items-center gap-2 text-base">
                  <span class="etichetta" :class="PRIORITA[a.priorita].classe">{{ PRIORITA[a.priorita].nome }}</span>
                  <span class="min-w-0 flex-1 truncate font-semibold leading-tight">{{ a.titolo }}</span>
                  <span v-if="tuttiAvvisiDi(l).length > 1" class="tenue flex-none text-sm font-semibold">+{{ tuttiAvvisiDi(l).length - 1 }}</span>
                </li>
              </ul>
              <p v-if="l.stato.meteo_simulato" class="tenue text-sm">Meteo simulato: i dati reali non sono raggiungibili.</p>
              <NuxtLink :to="`/localita/${l.id}`" class="pulsante w-full !min-h-[2.9rem]">Gestisci avvisi</NuxtLink>
            </div>
          </article>
          </template>
        </div>

        <div class="flex-none pb-2 pt-1">
          <NuxtLink to="/localita/nuova" class="pulsante pulsante-scuro w-full !min-h-[3.75rem] !text-lg"><Plus aria-hidden="true" />Aggiungi nuova località</NuxtLink>
        </div>
      </section>
    </div>
  </div>
</template>
