<script setup lang="ts">
// Avvisi di un luogo: che cosa, a che distanza, quanto urgenti. Ogni scelta si salva subito.
import type { Map as MappaLibre, Marker } from 'maplibre-gl'
import { Bell, ChevronLeft } from '@lucide/vue'

definePageMeta({ layout: 'pieno' })

const route = useRoute()
const api = useApi()
const toast = useToast()
const avvisi = useAvvisi()
const idLoc = Number(route.params.id)

const l = ref<Localita | null>(null)
const stato = ref<'caricamento' | 'ok' | 'errore' | 'assente'>('caricamento')
const conferma = ref(false)
const mappa = shallowRef<MappaLibre>()
let marcatore: Marker | null = null

async function carica() {
  try {
    l.value = await api<Localita>(`/localita/${idLoc}`)
    stato.value = 'ok'
    disegna(true)
  } catch (e) {
    stato.value = (e as { statusCode?: number }).statusCode === 404 ? 'assente' : 'errore'
  }
}

function disegna(inquadrare = false) {
  const m = mappa.value
  const x = l.value
  if (!m || !x) return
  impostaZone(m, 'loc', x.stato.zone)
  const dati: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [cerchio(x.lat, x.lon, x.raggio_km * 1000)] }
  const s = m.getSource('raggio') as { setData: (d: GeoJSON.FeatureCollection) => void } | undefined
  if (s) s.setData(dati)
  else {
    m.addSource('raggio', { type: 'geojson', data: dati })
    m.addLayer({ id: 'raggio', type: 'line', source: 'raggio', paint: { 'line-color': '#14181f', 'line-width': 2, 'line-dasharray': [3, 2] } })
  }
  if (!marcatore) marcatore = mettiPin(m, x.lat, x.lon, { icona: x.tipo, classe: 'pin-selezionato' })
  if (inquadrare || s) {
    const r = x.raggio_km * 1000
    inquadra(m, [0, 90, 180, 270].map((g) => { const p = destino(x.lat, x.lon, g, r); return { lat: p[1], lon: p[0] } }), { margine: 24, zoomMax: 14 })
  }
}

function pronta(m: MappaLibre) {
  mappa.value = m
  disegna(true)
}

async function salva(campi: Partial<Pick<Localita, 'avvisi_attivi' | 'avvisi_tipi' | 'raggio_km' | 'urgenza'>>) {
  if (!l.value) return
  const prima = { ...l.value }
  Object.assign(l.value, campi)
  try {
    l.value = await api<Localita>(`/localita/${idLoc}`, { method: 'PATCH', body: campi })
    disegna()
    toast.ok('Salvato')
    avvisi.aggiorna()
  } catch (e) {
    l.value = prima as Localita
    toast.errore(messaggioErrore(e))
  }
}

function alternaTipo(t: TipoSegnalazione) {
  if (!l.value) return
  const insieme = new Set(l.value.avvisi_tipi)
  if (insieme.has(t)) insieme.delete(t)
  else insieme.add(t)
  if (!insieme.size) { toast.errore('Scegli almeno un tipo di avviso.'); return }
  salva({ avvisi_tipi: [...insieme] })
}

async function rimuovi() {
  try {
    await api(`/localita/${idLoc}`, { method: 'DELETE' })
    conferma.value = false
    toast.ok('Località rimossa')
    avvisi.aggiorna()
    await navigateTo('/localita')
  } catch (e) {
    toast.errore(messaggioErrore(e))
  }
}

const mieiAvvisi = computed(() => avvisi.lista.value.filter((a) => a.localita_id === idLoc))
const URGENZE: { v: Urgenza; titolo: string; chip: Priorita }[] = [
  { v: 'urgenti', titolo: 'Solo urgenti', chip: 'urgente' },
  { v: 'urgenti_importanti', titolo: 'Urgenti e importanti', chip: 'importante' },
  { v: 'tutti', titolo: 'Tutti', chip: 'informazione' },
]
const AIUTO_URGENZA: Record<Urgenza, string> = { urgenti: 'Fuoco entro 2 km', urgenti_importanti: 'Anche fumo e fuoco più lontano', tutti: 'Anche rischio alto oggi e terreni a rischio' }

onMounted(carica)
onBeforeUnmount(() => marcatore?.remove())
</script>

<template>
  <div class="scorri flex flex-col gap-3 px-4 pb-6 pt-3">
    <div class="flex items-center gap-3">
      <NuxtLink to="/localita" class="indietro"><ChevronLeft class="size-6" aria-hidden="true" />Indietro</NuxtLink>
      <h1 class="titolo flex-1 truncate text-center text-[1.6rem]">{{ l?.nome ?? '' }}</h1>
      <span v-if="l" class="etichetta" :class="LIVELLI[l.stato.livello].classe">{{ LIVELLI[l.stato.livello].nome }}</span>
    </div>

    <template v-if="stato === 'caricamento'">
      <div class="scheletro h-40" /><div class="scheletro h-14" /><div class="scheletro h-32" />
    </template>
    <StatoErrore v-else-if="stato === 'errore'" @riprova="carica" />
    <StatoVuoto v-else-if="stato === 'assente'">
      <template #icona><IconaTipo tipo="altro" class="size-8" /></template>
      <template #titolo>Località non trovata</template>
      Forse è stata rimossa.
      <template #azione><NuxtLink to="/localita" class="pulsante pulsante-scuro w-full">Torna alle località</NuxtLink></template>
    </StatoVuoto>

    <template v-else-if="l">
      <div class="h-44 flex-none overflow-hidden rounded-3xl border-[1.5px] border-linea"><MappaBase :centro="[l.lon, l.lat]" :zoom="12" :limiti="false" @pronta="pronta" /></div>
      <p class="tenue -mt-1 text-sm">
        {{ plurale(l.stato.n_zone, 'zona', 'zone') }} a rischio entro {{ l.raggio_km }} km · {{ plurale(l.stato.n_segnalazioni, 'segnalazione', 'segnalazioni') }} attive
        <template v-if="l.stato.meteo_simulato"> · meteo simulato</template>
      </p>

      <section v-if="mieiAvvisi.length" class="scheda flex flex-col gap-2 !border-brace">
        <h2 class="sottotitolo">In corso adesso</h2>
        <ul class="flex flex-col gap-2">
          <li v-for="a in mieiAvvisi" :key="a.id" class="flex items-start gap-2">
            <span class="etichetta mt-0.5" :class="PRIORITA[a.priorita].classe">{{ PRIORITA[a.priorita].nome }}</span>
            <span class="text-base font-bold leading-snug">{{ a.titolo }}<span class="tenue block font-normal">{{ a.testo }}</span></span>
          </li>
        </ul>
      </section>

      <div class="riga scheda !min-h-14 !py-1">
        <Bell class="size-6 flex-none" aria-hidden="true" />
        <span class="flex-1 text-lg font-extrabold">Avvisi per {{ l.nome }}</span>
        <Interruttore :model-value="l.avvisi_attivi" :nome="`Avvisi per ${l.nome}`" @update:model-value="salva({ avvisi_attivi: $event })" />
      </div>

      <section v-if="l.avvisi_attivi && avvisi.permesso.value === 'default'" class="scheda flex flex-col gap-2 !border-cielo bg-cielo-fondo">
        <p class="text-base font-semibold">Per ricevere gli avvisi anche quando guardi altro, consenti le notifiche.</p>
        <button type="button" class="pulsante pulsante-scuro" @click="avvisi.richiediPermesso()">Consenti le notifiche</button>
      </section>
      <p v-else-if="l.avvisi_attivi && avvisi.permesso.value === 'denied'" class="tenue text-base">Le notifiche sono bloccate nelle impostazioni del browser: gli avvisi compaiono comunque dentro l’app.</p>

      <template v-if="l.avvisi_attivi">
        <h2 class="etichetta-campo mt-1">Di cosa vuoi essere avvisato?</h2>
        <div class="grid grid-cols-3 gap-2" role="group" aria-label="Tipi di avviso">
          <TesseraTipo v-for="t in (['fuoco', 'fumo', 'area_a_rischio'] as const)" :key="t" :tipo="t" :attiva="l.avvisi_tipi.includes(t)" :spenta="true" piccola breve @click="alternaTipo(t)" />
        </div>

        <h2 class="etichetta-campo mt-1">Fino a che distanza?</h2>
        <div class="segmenti" role="group" aria-label="Distanza">
          <button v-for="k in ([2, 5, 10] as const)" :key="k" type="button" :aria-pressed="l.raggio_km === k" @click="salva({ raggio_km: k })">{{ k }} km</button>
        </div>

        <h2 class="etichetta-campo mt-1">Quanto urgenti?</h2>
        <div class="flex flex-col gap-2" role="radiogroup" aria-label="Urgenza degli avvisi">
          <button v-for="u in URGENZE" :key="u.v" type="button" role="radio" class="opzione" :aria-checked="l.urgenza === u.v" @click="salva({ urgenza: u.v })">
            <span class="flex-1"><span class="block text-lg leading-tight">{{ u.titolo }}</span><span class="tenue block text-sm font-semibold">{{ AIUTO_URGENZA[u.v] }}</span></span>
            <span class="etichetta" :class="PRIORITA[u.chip].classe">{{ PRIORITA[u.chip].nome }}</span>
            <span class="radio" />
          </button>
        </div>
      </template>

      <button type="button" class="pulsante pulsante-fantasma pulsante-pericolo mx-auto mt-2" @click="conferma = true">Rimuovi questa località</button>

      <Foglio v-model="conferma" titolo="Rimuovere la località?">
        <h2 class="titolo mb-2 text-2xl">Rimuovere {{ l.nome }}?</h2>
        <p class="tenue mb-4 text-lg">Non riceverai più avvisi per questo luogo. Le tue segnalazioni restano nello storico.</p>
        <div class="flex gap-3">
          <button type="button" class="pulsante flex-1" @click="conferma = false">Annulla</button>
          <button type="button" class="pulsante pulsante-scuro !border-brace !bg-brace flex-1" @click="rimuovi">Rimuovi</button>
        </div>
      </Foglio>
    </template>
  </div>
</template>
