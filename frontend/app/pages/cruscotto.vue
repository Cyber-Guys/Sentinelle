<script setup lang="ts">
import maplibregl from 'maplibre-gl'
import { Flame, Check, Ban, Radio } from '@lucide/vue'

const { chiama, urlFoto } = useApi()

const coda = ref<Segnalazione[]>([])
const selezionata = ref<number | null>(null)
const errore = ref('')
const contenitore = ref<HTMLElement | null>(null)
let mappa: maplibregl.Map | null = null
let timer: ReturnType<typeof setInterval> | undefined

const scheda = computed(() => coda.value.find((s) => s.id === selezionata.value) ?? null)

const ora = (iso: string) => new Date(iso).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'medium' })

function geojsonCoda() {
  return {
    type: 'FeatureCollection' as const,
    features: coda.value.map((s) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [s.lon, s.lat] },
      properties: { id: s.id, colore: colorePriorita(s.priorita), selezionata: s.id === selezionata.value ? 1 : 0 },
    })),
  }
}

function aggiornaMappa() {
  (mappa?.getSource('coda') as maplibregl.GeoJSONSource | undefined)?.setData(geojsonCoda())
}

async function aggiorna() {
  try {
    coda.value = await chiama<Segnalazione[]>('/segnalazioni?stato=nuova')
    if (selezionata.value && !scheda.value) selezionata.value = null
    errore.value = ''
    aggiornaMappa()
  } catch (e: any) { errore.value = 'Server non raggiungibile' }
}

watch(selezionata, aggiornaMappa)

onMounted(() => {
  mappa = new maplibregl.Map({ container: contenitore.value!, style: stileOsm, center: [9.0, 40.05], zoom: 7.3 })
  mappa.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
  mappa.on('load', () => {
    const m = mappa!
    m.addSource('hotspot', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
    m.addLayer({ id: 'hotspot', type: 'circle', source: 'hotspot', paint: { 'circle-radius': 6, 'circle-color': '#7c2d12', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } })
    m.addSource('coda', { type: 'geojson', data: geojsonCoda() })
    m.addLayer({ id: 'coda', type: 'circle', source: 'coda', paint: {
      'circle-radius': ['case', ['==', ['get', 'selezionata'], 1], 15, 10],
      'circle-color': ['get', 'colore'], 'circle-opacity': 0.85,
      'circle-stroke-color': ['case', ['==', ['get', 'selezionata'], 1], '#111827', '#fff'], 'circle-stroke-width': 2.5,
    } })
    m.on('click', 'coda', (ev) => { selezionata.value = ev.features?.[0]?.properties?.id ?? null })
    m.on('mouseenter', 'coda', () => (m.getCanvas().style.cursor = 'pointer'))
    m.on('mouseleave', 'coda', () => (m.getCanvas().style.cursor = ''))
    chiama<any>('/hotspot').then((g) => (m.getSource('hotspot') as maplibregl.GeoJSONSource).setData(g)).catch(() => {})
  })
  aggiorna()
  timer = setInterval(aggiorna, 3000)
})

onBeforeUnmount(() => { clearInterval(timer); mappa?.remove() })

function seleziona(s: Segnalazione) {
  selezionata.value = s.id
  mappa?.flyTo({ center: [s.lon, s.lat], zoom: Math.max(mappa.getZoom(), 11) })
}

async function azione(tipo: 'conferma' | 'archivia') {
  if (!scheda.value) return
  try {
    await chiama(`/segnalazioni/${scheda.value.id}/${tipo}`, { method: 'POST' })
    selezionata.value = null
    await aggiorna()
  } catch (e: any) { errore.value = 'Operazione non riuscita: ' + e.message }
}
</script>

<template>
  <main class="h-dvh flex">
    <aside class="w-[26rem] max-w-[45vw] flex flex-col border-r border-bordo bg-carta">
      <header class="flex items-center justify-between border-b border-bordo px-4 py-3">
        <h1 class="flex items-center gap-2 text-xl font-extrabold text-fuoco"><Flame class="size-6" /> Cruscotto</h1>
        <span class="flex items-center gap-1 text-xs text-testo-2"><Radio class="size-4 text-bosco" /> {{ coda.length }} in coda · aggiorna ogni 3 s</span>
      </header>
      <p v-if="errore" class="px-4 py-2 text-sm text-alta">{{ errore }}</p>

      <ul class="flex-1 overflow-y-auto">
        <li v-if="!coda.length" class="p-6 text-center text-sm text-testo-2">Nessuna segnalazione nuova.</li>
        <li v-for="s in coda" :key="s.id">
          <button class="flex w-full items-center gap-3 border-b border-bordo px-4 py-3 text-left hover:bg-orange-50" :class="s.id === selezionata ? 'bg-orange-50' : ''" @click="seleziona(s)">
            <span class="flex size-11 shrink-0 items-center justify-center rounded-full font-extrabold text-white" :style="{ background: colorePriorita(s.priorita) }">{{ s.priorita }}</span>
            <span class="min-w-0">
              <span class="block font-semibold">{{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}</span>
              <span class="block text-xs text-testo-2">{{ ora(s.creata_il) }} · #{{ s.id }}</span>
            </span>
          </button>
        </li>
      </ul>

      <section v-if="scheda" class="max-h-[55%] space-y-3 overflow-y-auto border-t-2 border-fuoco bg-fondo p-4">
        <div class="flex items-center justify-between">
          <h2 class="font-bold">Segnalazione #{{ scheda.id }}</h2>
          <span class="rounded-full px-3 py-0.5 text-sm font-bold text-white" :style="{ background: colorePriorita(scheda.priorita) }">{{ etichettaPriorita(scheda.priorita) }} · {{ scheda.priorita }}</span>
        </div>
        <p class="text-xs text-testo-2">{{ ora(scheda.creata_il) }} · {{ scheda.lat.toFixed(4) }}, {{ scheda.lon.toFixed(4) }}</p>
        <img v-if="scheda.foto_url" :src="urlFoto(scheda.foto_url)!" alt="Foto della segnalazione" class="max-h-48 w-full rounded-lg object-cover" />
        <ul class="list-disc space-y-1 pl-5 text-sm">
          <li v-for="m in scheda.motivazioni" :key="m">{{ m }}</li>
        </ul>
        <div class="grid grid-cols-2 gap-2">
          <button class="secondario flex items-center justify-center gap-1 py-3" @click="azione('conferma')"><Check class="size-5" /> Conferma</button>
          <button class="flex items-center justify-center gap-1 rounded-xl border border-bordo bg-carta py-3 font-semibold" @click="azione('archivia')"><Ban class="size-5" /> Falso allarme</button>
        </div>
      </section>
    </aside>

    <div ref="contenitore" class="flex-1" />
  </main>
</template>
