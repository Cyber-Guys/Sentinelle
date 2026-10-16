<script setup lang="ts">
// Storico: le mie segnalazioni con posizione, foto o video, e che fine hanno fatto.
import type { Map as MappaLibre, Marker } from 'maplibre-gl'
import { Camera, Play } from '@lucide/vue'

const api = useApi()
const { id } = useSessione()
const eventi = useEventi()

const dati = ref<{ casa_nome: string | null; segnalazioni: RigaStorico[] } | null>(null)
const luoghi = ref<Localita[]>([])
const stato = ref<'caricamento' | 'ok' | 'errore'>('caricamento')
const filtro = ref<'tutte' | TipoSegnalazione>('tutte')
const quante = ref(6)
const aperta = ref<RigaStorico | null>(null)
const mappa = shallowRef<MappaLibre>()
let pin: Marker[] = []

const tutte = computed(() => dati.value?.segnalazioni ?? [])
const filtrate = computed(() => tutte.value.filter((s) => filtro.value === 'tutte' || s.tipo === filtro.value))
const visibili = computed(() => filtrate.value.slice(0, quante.value))

const FILTRI: { v: 'tutte' | TipoSegnalazione; nome: string }[] = [
  { v: 'tutte', nome: 'Tutte' }, { v: 'fuoco', nome: 'Incendio' }, { v: 'fumo', nome: 'Fumo' }, { v: 'area_a_rischio', nome: 'Terreno' },
]
const STATO: Record<string, { nome: string; classe: string }> = {
  nuova: { nome: 'In verifica', classe: 'e-cielo' }, confermata: { nome: 'Confermata', classe: 'e-macchia' }, archiviata: { nome: 'Non confermata', classe: '' },
}

async function carica() {
  try {
    const [d, l] = await Promise.all([api<typeof dati.value>(`/utenti/${id.value}/storico`), api<Localita[]>(`/utenti/${id.value}/localita`)])
    dati.value = d
    luoghi.value = l
    stato.value = 'ok'
    disegna()
  } catch {
    stato.value = 'errore'
  }
}

function disegna() {
  const m = mappa.value
  if (!m) return
  pin.forEach((p) => p.remove())
  pin = [
    ...visibili.value.map((s, i) => mettiPin(m, s.lat, s.lon, { icona: s.tipo, classe: 'pin-piccolo', testo: String(i + 1), nome: `${TIPI[s.tipo].nome}, segnalazione ${i + 1}` })),
    ...luoghi.value.filter((l) => l.tipo === 'casa').map((l) => mettiPin(m, l.lat, l.lon, { icona: 'casa', classe: 'pin-piccolo', nome: l.nome })),
  ]
  inquadra(m, [...visibili.value, ...luoghi.value.filter((l) => l.tipo === 'casa')], { margine: 36, zoomMax: 13 })
}

watch([filtro, quante], () => nextTick(disegna))

const vediSulMappa = (s: RigaStorico) => navigateTo({ path: '/', query: { punto: `${s.lat},${s.lon}`, seg: String(s.id) } })

let disiscrivi: (() => void) | null = null
onMounted(() => {
  carica()
  // l'operatore conferma o archivia dal cruscotto: qui lo stato cambia da solo
  disiscrivi = eventi.on('segnalazione_valutata', carica)
})
onBeforeUnmount(() => { disiscrivi?.(); pin.forEach((p) => p.remove()) })
</script>

<template>
  <div class="scorri flex flex-col gap-2.5 px-4 pb-4 pt-3.5">
    <header class="flex items-center gap-2">
      <h1 class="titolo flex-1 text-[1.65rem]">Le mie segnalazioni</h1>
      <span v-if="stato === 'ok'" class="etichetta !text-base">{{ dati!.segnalazioni.length }} in tutto</span>
    </header>

    <template v-if="stato === 'caricamento'">
      <div class="scheletro h-12" /><div class="scheletro h-32" /><div class="scheletro h-36" /><div class="scheletro h-36" />
    </template>
    <StatoErrore v-else-if="stato === 'errore'" @riprova="carica" />
    <StatoVuoto v-else-if="!tutte.length">
      <template #icona><Camera class="size-8" aria-hidden="true" /></template>
      <template #titolo>Nessuna segnalazione</template>
      Quando segnali un incendio, del fumo o un terreno a rischio, lo ritrovi qui con la foto e il punto sulla mappa.
      <template #azione><NuxtLink to="/" class="gigante !min-h-[4.25rem] !text-xl">Vai alla mappa</NuxtLink></template>
    </StatoVuoto>

    <template v-else>
      <div class="senza-barra -mx-4 flex gap-2 overflow-x-auto px-4 pb-1" role="group" aria-label="Filtra per tipo">
        <button v-for="f in FILTRI" :key="f.v" type="button" class="scelta !min-h-11 !text-base" :aria-pressed="filtro === f.v" @click="filtro = f.v">{{ f.nome }}</button>
      </div>

      <div class="h-[8.5rem] flex-none overflow-hidden rounded-3xl border-[1.5px] border-linea"><MappaBase :centro="[8.9, 39.45]" :zoom="9" :interattiva="false" @pronta="(m) => { mappa = m; disegna() }" /></div>

      <p v-if="!filtrate.length" class="tenue py-6 text-center text-lg">Nessuna segnalazione di questo tipo.</p>

      <article v-for="s in visibili" :key="s.id" class="scheda flex gap-3 !p-2.5">
        <button type="button" class="relative grid h-[7.5rem] w-24 flex-none place-items-center overflow-hidden rounded-2xl bg-vuoto text-testo-2" :disabled="!s.foto_url && !s.video_url" :aria-label="s.foto_url || s.video_url ? 'Apri foto o video' : 'Nessuna foto'" @click="aperta = s">
          <img v-if="s.foto_url" :src="urlMedia(s.foto_url)" alt="" class="size-full object-cover" loading="lazy">
          <video v-else-if="s.video_url" :src="urlMedia(s.video_url) + '#t=0.1'" class="size-full object-cover" muted playsinline preload="metadata" />
          <span v-else class="flex flex-col items-center gap-1 text-sm font-bold"><Camera class="size-7" aria-hidden="true" />senza foto</span>
          <span v-if="s.video_url" class="absolute bottom-1.5 left-1.5 grid size-7 place-items-center rounded-full bg-inchiostro/85 text-white"><Play class="size-3.5" fill="currentColor" aria-hidden="true" /></span>
        </button>
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="tile-tipo !size-9 !rounded-lg" :class="`t-${s.tipo}`"><IconaTipo :tipo="s.tipo" aria-hidden="true" /></span>
            <h2 class="flex-1 truncate text-xl font-extrabold">{{ TIPI[s.tipo].nome }}</h2>
          </div>
          <p class="text-base font-semibold leading-tight">{{ dataBreve(s.creata_il) }}<template v-if="s.km_casa != null"> · {{ daCasa(s.km_casa, dati!.casa_nome) }}</template></p>
          <p class="tenue truncate text-sm">{{ s.comune ?? 'Sardegna' }}<template v-if="s.nota"> · “{{ s.nota }}”</template></p>
          <div class="mt-auto flex flex-wrap items-center gap-2">
            <button type="button" class="pulsante pulsante-piccolo" @click="vediSulMappa(s)">Vedi sulla mappa</button>
            <span class="etichetta" :class="STATO[s.stato]?.classe">{{ STATO[s.stato]?.nome }}</span>
          </div>
        </div>
      </article>

      <button v-if="filtrate.length > quante" type="button" class="pulsante !min-h-14" @click="quante += 6">Mostra le altre {{ filtrate.length - quante }}</button>
    </template>

    <!-- foto o video a tutta larghezza -->
    <Foglio :model-value="!!aperta" titolo="Foto o video" @update:model-value="aperta = null">
      <template v-if="aperta">
        <img v-if="aperta.foto_url" :src="urlMedia(aperta.foto_url)" :alt="`${TIPI[aperta.tipo].nome}, ${dataBreve(aperta.creata_il)}`" class="w-full rounded-2xl">
        <video v-if="aperta.video_url" :src="urlMedia(aperta.video_url)" class="mt-3 w-full rounded-2xl" controls playsinline preload="metadata" />
        <p v-if="aperta.nota" class="mt-3 text-lg">{{ aperta.nota }}</p>
        <button type="button" class="pulsante pulsante-scuro mt-4 w-full" @click="aperta = null">Chiudi</button>
      </template>
    </Foglio>
  </div>
</template>
