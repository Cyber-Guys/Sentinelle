<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { Flame, Plus, X, MapPin, LocateFixed, Camera, Star } from '@lucide/vue'

const { chiama, urlFoto } = useApi()

const CENTRI: Record<string, [number, number]> = {
  SERRAMANNA: [8.92, 39.42],
  VILLASOR: [8.94, 39.38],
}

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

const FILTRI = [
  { id: '2025', etichetta: '2025', da: 2025 },
  { id: '5', etichetta: 'Ultimi 5 anni', da: 2021 },
  { id: 'tutti', etichetta: 'Dal 2015', da: 2015 },
] as const
const filtro = ref<(typeof FILTRI)[number]['id']>('2025')
const caricando = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
let richiesta = 0

const contenitore = ref<HTMLElement | null>(null)
let mappa: maplibregl.Map | null = null
let marcatore: maplibregl.Marker | null = null

const centro = computed<[number, number]>(() => CENTRI[utente.value?.comune ?? ''] ?? [8.9, 40.1])
const coloreRischio = computed(() =>
  rischio.value?.livello === 'alto' ? 'bg-alta' : rischio.value?.livello === 'medio' ? 'bg-media' : 'bg-bassa',
)

onMounted(async () => {
  try {
    utenti.value = await chiama<Utente[]>('/utenti')
    const salvato = (() => { try { return Number(localStorage.getItem('utenteId')) } catch { return 0 } })()
    const trovato = utenti.value.find((u) => u.id === salvato)
    if (trovato) await scegli(trovato)
  } catch (e: any) { errore.value = 'Server non raggiungibile: ' + e.message }
})

onBeforeUnmount(() => { clearTimeout(timer); mappa?.remove() })

async function scegli(u: Utente) {
  utente.value = u
  try { localStorage.setItem('utenteId', String(u.id)) } catch {}
  rischio.value = null
  chiama<Rischio>(`/rischio?lat=${centro.value[1]}&lon=${centro.value[0]}`).then((r) => (rischio.value = r)).catch(() => {})
  await nextTick()
  avviaMappa()
}

function cambiaUtente() {
  mappa?.remove(); mappa = null; marcatore = null
  utente.value = null; pannello.value = false; esito.value = null
  try { localStorage.removeItem('utenteId') } catch {}
}

// piu' recente = rosso intenso, piu' vecchio = giallo tenue
const COLORE_ANNO: any = ['interpolate', ['linear'], ['get', 'anno'], 2015, '#fde68a', 2020, '#fb923c', 2025, '#dc2626']

function avviaMappa() {
  if (!contenitore.value) return
  mappa = new maplibregl.Map({ container: contenitore.value, style: stileOsm, center: centro.value, zoom: 12 })
  mappa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
  mappa.on('load', () => {
    const m = mappa!
    m.addSource('storico', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
    m.addLayer({ id: 'storico-riempimento', type: 'fill', source: 'storico', paint: { 'fill-color': COLORE_ANNO, 'fill-opacity': 0.35 } })
    m.addLayer({ id: 'storico-linea', type: 'line', source: 'storico', paint: { 'line-color': COLORE_ANNO, 'line-width': 0.6, 'line-opacity': 0.8 } })
    m.addSource('hotspot', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
    m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 8, 'circle-color': '#f97316', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } })
    m.on('click', 'storico-riempimento', (ev) => {
      const p = ev.features?.[0]?.properties
      if (!p || pannello.value) return
      new maplibregl.Popup().setLngLat(ev.lngLat)
        .setHTML(`<b>${p.data ?? 'data n.d.'}</b> (${p.anno})<br>${p.ettari_totali != null ? Number(p.ettari_totali).toFixed(1) + ' ettari' : 'ettari n.d.'}`)
        .addTo(m)
    })
    m.on('click', (ev) => {
      if (!pannello.value) return
      impostaPos(ev.lngLat.lat, ev.lngLat.lng)
    })
    m.on('moveend', pianificaStorico)
    caricaStorico()
    chiama<any>('/hotspot').then((g) => (m.getSource('hotspot') as maplibregl.GeoJSONSource).setData(g)).catch(() => {})
  })
}

function pianificaStorico() {
  clearTimeout(timer)
  timer = setTimeout(caricaStorico, 300)
}

watch(filtro, pianificaStorico)

async function caricaStorico() {
  if (!mappa) return
  const b = mappa.getBounds()
  const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(',')
  const da = FILTRI.find((f) => f.id === filtro.value)!.da
  const mia = ++richiesta
  caricando.value = true
  try {
    const g = await chiama<any>(`/storico/incendi?bbox=${bbox}&anno_da=${da}&anno_a=2025`)
    if (mia === richiesta) (mappa?.getSource('storico') as maplibregl.GeoJSONSource | undefined)?.setData(g)
  } catch {}
  if (mia === richiesta) caricando.value = false
}

function impostaPos(lat: number, lon: number) {
  pos.value = { lat, lon }
  if (!mappa) return
  marcatore ??= new maplibregl.Marker({ color: '#ea580c' })
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
    utenti.value = await chiama<Utente[]>('/utenti')
    utente.value = utenti.value.find((u) => u.id === utente.value!.id) ?? utente.value
  } catch (e: any) { errore.value = 'Invio non riuscito: ' + e.message }
  inCorso.value = false
}
</script>

<template>
  <main class="h-dvh flex flex-col">
    <!-- scelta utente -->
    <section v-if="!utente" class="flex-1 flex flex-col items-center justify-center gap-4 p-6">
      <h1 class="flex items-center gap-2 text-3xl font-extrabold text-fuoco"><Flame class="size-8" /> Sentinelle</h1>
      <p class="text-testo-2">Chi sei?</p>
      <p v-if="errore" class="text-alta text-sm">{{ errore }}</p>
      <button v-for="u in utenti" :key="u.id" class="w-full max-w-sm rounded-xl border border-bordo bg-carta p-4 text-left active:bg-bosco-chiaro" @click="scegli(u)">
        <span class="font-bold">{{ u.nome }}</span>
        <span class="block text-sm text-testo-2">{{ u.comune }} · {{ u.punti }} punti</span>
      </button>
    </section>

    <template v-else>
      <header class="flex items-center justify-between gap-2 border-b border-bordo bg-carta px-4 py-2">
        <button class="text-left" @click="cambiaUtente">
          <span class="block font-bold leading-tight">{{ utente.nome }}</span>
          <span class="block text-xs text-testo-2">{{ utente.comune }}</span>
        </button>
        <span class="flex items-center gap-1 rounded-full bg-bosco-chiaro px-3 py-1 text-sm font-bold text-bosco"><Star class="size-4" /> {{ utente.punti }}</span>
        <span class="flex items-center gap-1.5 rounded-full border border-bordo px-3 py-1 text-xs">
          Rischio oggi
          <span v-if="rischio" class="rounded-full px-2 py-0.5 font-bold text-white capitalize" :class="coloreRischio">{{ rischio.livello }}</span>
          <span v-else class="text-testo-2">…</span>
        </span>
      </header>

      <div class="relative flex-1 min-h-[180px] flex flex-col">
        <div ref="contenitore" class="flex-1" />
        <div class="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-carta/95 p-1 text-xs shadow">
          <button v-for="f in FILTRI" :key="f.id" type="button" class="rounded-full px-2.5 py-1 font-semibold" :class="filtro === f.id ? 'bg-fuoco text-white' : 'text-testo-2'" @click="filtro = f.id">{{ f.etichetta }}</button>
        </div>
        <span v-if="caricando" class="absolute left-2 top-11 rounded-full bg-carta/95 px-2.5 py-1 text-xs text-testo-2 shadow">caricamento…</span>
      </div>

      <div v-if="!pannello" class="p-4 bg-carta border-t border-bordo">
        <button class="primario w-full py-5 text-2xl flex items-center justify-center gap-2" @click="apri"><Plus class="size-7" /> Segnala</button>
      </div>

      <section v-else class="max-h-[58vh] overflow-y-auto border-t border-bordo bg-carta p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-bold">{{ esito ? 'Segnalazione inviata' : 'Nuova segnalazione' }}</h2>
          <button aria-label="Chiudi" class="p-1" @click="chiudi"><X /></button>
        </div>

        <!-- esito -->
        <div v-if="esito" class="space-y-3">
          <div class="flex items-center gap-4">
            <div class="flex size-20 items-center justify-center rounded-full text-3xl font-extrabold text-white" :style="{ background: colorePriorita(esito.priorita) }">{{ esito.priorita }}</div>
            <div>
              <p class="font-bold">Priorita {{ etichettaPriorita(esito.priorita).toLowerCase() }}</p>
              <p class="text-sm text-testo-2">Grazie, la segnalazione e in coda agli operatori.</p>
            </div>
          </div>
          <ul class="list-disc space-y-1 pl-5 text-sm">
            <li v-for="m in esito.motivazioni" :key="m">{{ m }}</li>
          </ul>
          <button class="secondario w-full py-3" @click="chiudi">Fatto</button>
        </div>

        <!-- modulo -->
        <form v-else class="space-y-3" @submit.prevent="invia">
          <div class="grid grid-cols-2 gap-2">
            <button type="button" class="rounded-xl border-2 p-3 font-semibold" :class="tipo === 'fuoco' ? 'border-fuoco bg-orange-50 text-fuoco-scuro' : 'border-bordo'" @click="tipo = 'fuoco'">Fuoco / fumo</button>
            <button type="button" class="rounded-xl border-2 p-3 font-semibold" :class="tipo === 'area_a_rischio' ? 'border-bosco bg-bosco-chiaro text-bosco' : 'border-bordo'" @click="tipo = 'area_a_rischio'">Area a rischio</button>
          </div>

          <label class="flex items-center gap-2 rounded-xl border border-dashed border-bordo p-3 text-sm">
            <Camera class="size-5 text-testo-2" />
            <span class="truncate">{{ foto ? foto.name : 'Aggiungi una foto (facoltativa)' }}</span>
            <input type="file" accept="image/*" capture="environment" class="hidden" @change="foto = ($event.target as HTMLInputElement).files?.[0] ?? null" />
          </label>

          <div class="space-y-2">
            <button type="button" class="flex w-full items-center justify-center gap-2 rounded-xl border border-bordo p-3 font-semibold" @click="usaGps"><LocateFixed class="size-5" /> Usa la mia posizione</button>
            <p class="flex items-center gap-1 text-sm" :class="pos ? 'text-bosco font-semibold' : 'text-testo-2'">
              <MapPin class="size-4" />
              {{ pos ? `Posizione scelta: ${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}` : 'Oppure tocca la mappa per indicare il punto' }}
            </p>
          </div>

          <p v-if="errore" class="text-sm text-alta">{{ errore }}</p>
          <button class="primario w-full py-4 text-lg disabled:opacity-50" :disabled="!pos || inCorso">{{ inCorso ? 'Invio…' : 'Invia segnalazione' }}</button>
        </form>
      </section>
    </template>
  </main>
</template>
