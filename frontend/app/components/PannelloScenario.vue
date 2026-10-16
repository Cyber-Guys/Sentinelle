<script setup lang="ts">
import { Flame, X, Play, Pause, RotateCcw, Navigation2, Droplets, Droplet, Info, MapPin, Building2, Waves, ChevronDown } from '@lucide/vue'
import type { Simulazione } from '~/composables/useMappa'

// Pannello dello scenario di propagazione (cruscotto): desktop `sospeso` al posto della scheda, telefono dentro il foglio.
// v-model:ore = orizzonte (cambiarlo rilancia la simulazione nel genitore), v-model:cursore = ora mostrata sulla mappa.
const props = defineProps<{ titolo: string; dati: Simulazione | null; caricamento: boolean; errore: string; telefono?: boolean; padFondo?: number }>()
const emit = defineEmits<{ chiudi: []; riprova: []; vai: [lon: number, lat: number] }>()
const ore = defineModel<number>('ore', { required: true })
const cursore = defineModel<number>('cursore', { required: true })

const ORIZZONTI = [1, 3, 6, 12, 24]
const nome = useId()
const fotogramma = computed(() => props.dati?.fotogrammi.find((f) => f.ora === cursore.value) ?? props.dati?.fotogrammi.at(-1) ?? null)
const ettari = useConteggio(() => Math.round(fotogramma.value?.ettari ?? 0))
const fmt = (n: number) => n.toLocaleString('it-IT')
const orario = computed(() => {
  if (!props.dati) return ''
  const t = new Date(new Date(props.dati.inizio).getTime() + cursore.value * 3600_000)
  return t.toLocaleTimeString('it-IT', { timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit' })
})
const PUNTI = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest']
const daDove = (g: number) => PUNTI[Math.round(((g % 360) + 360) % 360 / 45) % 8]
// la freccia indica dove spinge il vento (verso cui soffia), non da dove viene
const rotazione = computed(() => ((fotogramma.value?.vento.da_gradi ?? 0) + 180) % 360)
const comuni = computed(() => [...(props.dati?.comuni ?? [])].sort((a, b) => a.raggiunto_ora - b.raggiunto_ora))
const origine = computed(() => props.dati?.origine?.comune ?? '')
const altri = computed(() => comuni.value.filter((c) => c.nome !== origine.value && c.raggiunto_ora <= cursore.value).length)
const invasi = computed(() => (props.dati?.acqua ?? []).filter((a) => a.tipo === 'invaso'))
const puntiAcqua = computed(() => (props.dati?.acqua ?? []).filter((a) => a.tipo !== 'invaso'))
const apriPunti = ref(false)
const tacche = computed(() => Array.from({ length: props.dati?.ore ?? ore.value }, (_, i) => i + 1))
const passoEtichette = computed(() => { const n = tacche.value.length; return n <= 6 ? 1 : n <= 12 ? 3 : 6 })
const conEtichetta = (h: number) => h === 1 || h === tacche.value.length || h % passoEtichette.value === 0
// dal testo del backend si mostra solo cio' che aggiunge alla nota fissa (es. meteo simulato)
const notaMeteo = computed(() => props.dati?.note.match(/Meteo[^.]*\./)?.[0] ?? '')
const progresso = computed(() => (props.dati && props.dati.ore > 1 ? (cursore.value - 1) / (props.dati.ore - 1) : 1))

// riproduzione: ~0,6 s per ora, si ferma alla fine; dalla fine riparte da +1 h
const inRiproduzione = ref(false)
let timer: ReturnType<typeof setInterval> | undefined
function ferma() { inRiproduzione.value = false; clearInterval(timer) }
function alternaPlay() {
  if (!props.dati) return
  if (inRiproduzione.value) return ferma()
  if (cursore.value >= props.dati.ore) cursore.value = 1
  inRiproduzione.value = true
  timer = setInterval(() => {
    if (!props.dati || cursore.value >= props.dati.ore) return ferma()
    cursore.value++
  }, 600)
}
watch(() => props.dati, ferma)
onBeforeUnmount(ferma)
const allaFine = computed(() => !!props.dati && cursore.value >= props.dati.ore && !inRiproduzione.value)
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <header class="flex shrink-0 items-start justify-between gap-3 border-b border-bordo" :class="telefono ? 'px-4 pt-1 pb-3' : 'px-5 py-3.5'">
      <div class="min-w-0">
        <p class="flex items-center gap-2 text-[.72rem] text-testo-3">
          <span class="flex items-center gap-1 rounded-full bg-brace/12 px-2 py-px font-medium text-brace"><Flame class="size-3" aria-hidden="true" />Scenario</span>
          <span v-if="dati" class="cifre">dalle {{ new Date(dati.inizio).toLocaleTimeString('it-IT', { timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit' }) }} · meteo ora per ora</span>
        </p>
        <h2 id="titolo-scenario" class="mt-1 truncate text-base font-semibold">Scenario da {{ dati?.origine?.comune ? nomeComune(dati.origine.comune) : titolo }}</h2>
      </div>
      <button type="button" aria-label="Chiudi scenario" class="secondario tocco flex size-8 shrink-0 items-center justify-center" @click="emit('chiudi')"><X class="size-4" aria-hidden="true" /></button>
    </header>

    <div class="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain" :class="telefono ? 'px-4 pt-3' : 'px-5 py-4'" :style="padFondo ? { paddingBottom: `${padFondo}px` } : undefined">
      <!-- orizzonte: cambiarlo rilancia la simulazione -->
      <div class="flex items-center gap-3">
        <span class="etichetta shrink-0">Orizzonte</span>
        <div class="flex flex-1 rounded-full bg-vetro p-0.5 ring-1 ring-bordo" role="radiogroup" aria-label="Orizzonte della simulazione">
          <label v-for="o in ORIZZONTI" :key="o" class="flex flex-1 cursor-pointer items-center justify-center rounded-full text-[.76rem] font-medium whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="[telefono ? 'h-11' : 'h-8', ore === o ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo']">
            <input v-model="ore" type="radio" :name="nome" :value="o" class="sr-only" /><span class="cifre">{{ o }} h</span>
          </label>
        </div>
      </div>

      <StatoErrore v-if="errore && !caricamento" compatto titolo="Simulazione non riuscita" :messaggio="errore" @riprova="emit('riprova')" />

      <template v-else>
        <!-- ora corrente + riproduzione -->
        <div class="vetro p-3">
          <div class="flex items-center gap-3">
            <button type="button" class="flex size-11 shrink-0 items-center justify-center rounded-full bg-vetro-forte text-brace ring-1 ring-bordo-luce transition-colors hover:bg-brace/12 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cielo" :disabled="!dati || caricamento" :aria-label="inRiproduzione ? 'Pausa' : allaFine ? 'Riproduci da capo' : 'Riproduci'" @click="alternaPlay">
              <Pause v-if="inRiproduzione" class="size-5" aria-hidden="true" /><RotateCcw v-else-if="allaFine" class="size-5" aria-hidden="true" /><Play v-else class="size-5 translate-x-px" aria-hidden="true" />
            </button>
            <p v-if="dati && !caricamento" class="cifre min-w-0 leading-none" aria-live="polite">
              <span class="text-[1.75rem] font-semibold tracking-tight">+{{ cursore }} h</span>
              <span class="ml-1.5 text-[1rem] text-testo-2">· {{ orario }}</span>
            </p>
            <span v-else class="scheletro h-8 w-36 rounded-s" />
          </div>
          <div class="mt-3">
            <input v-model.number="cursore" type="range" min="1" :max="dati?.ore ?? ore" step="1" class="cursore-scenario w-full" :style="{ '--p': progresso }" :disabled="!dati || caricamento" aria-label="Ora dello scenario" @input="ferma" />
            <div class="relative mx-[9px] mt-0.5 h-5" aria-hidden="true">
              <span v-for="h in tacche" :key="h" class="absolute top-0 flex -translate-x-1/2 flex-col items-center" :style="{ left: tacche.length > 1 ? `${((h - 1) / (tacche.length - 1)) * 100}%` : '50%' }">
                <span class="w-px rounded-full" :class="[conEtichetta(h) ? 'h-1.5' : 'h-1', h <= cursore ? 'bg-brace/70' : 'bg-testo-3/50']" />
                <span v-if="conEtichetta(h)" class="cifre mt-0.5 text-[.64rem] leading-none" :class="h === cursore ? 'font-semibold text-testo' : 'text-testo-3'">{{ h }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- grandezze dell'ora sul cursore -->
        <div class="grid grid-cols-3 items-stretch gap-2">
          <div class="vetro px-3 py-2.5">
            <p class="etichetta truncate">Area</p>
            <p v-if="fotogramma && !caricamento" class="cifre mt-1 leading-none"><span class="text-xl font-semibold text-brace">{{ fmt(ettari) }}</span> <span class="text-[.72rem] text-testo-2">ha</span></p>
            <span v-else class="scheletro mt-1 block h-5 w-14 rounded-s" />
            <p v-if="fotogramma && !caricamento" class="cifre mt-1 text-[.68rem] text-testo-3">fronte {{ fotogramma.fronte_km.toLocaleString('it-IT') }} km</p>
          </div>
          <div class="vetro px-3 py-2.5">
            <p class="etichetta truncate">Vento</p>
            <p v-if="fotogramma && !caricamento" class="cifre mt-1 flex items-center gap-1.5 leading-none">
              <Navigation2 class="size-4 shrink-0 fill-cielo text-cielo transition-transform duration-300" :style="{ rotate: `${rotazione}deg` }" aria-hidden="true" />
              <span class="text-xl font-semibold">{{ fotogramma.vento.kmh }}</span> <span class="text-[.72rem] text-testo-2">km/h</span>
            </p>
            <span v-else class="scheletro mt-1 block h-5 w-14 rounded-s" />
            <p v-if="fotogramma && !caricamento" class="mt-1 text-[.68rem] text-testo-3">da {{ daDove(fotogramma.vento.da_gradi) }}</p>
          </div>
          <div class="vetro px-3 py-2.5">
            <p class="etichetta truncate">Umidità</p>
            <p v-if="fotogramma && !caricamento" class="cifre mt-1 flex items-center gap-1.5 leading-none"><Droplets class="size-4 shrink-0 text-testo-3" aria-hidden="true" /><span class="text-xl font-semibold">{{ fotogramma.umidita }}</span> <span class="text-[.72rem] text-testo-2">%</span></p>
            <span v-else class="scheletro mt-1 block h-5 w-14 rounded-s" />
            <p v-if="fotogramma && !caricamento" class="mt-1 text-[.68rem]" :class="fotogramma.umidita < 30 ? 'text-ambra' : 'text-testo-3'">{{ fotogramma.umidita < 30 ? 'aria secca' : 'relativa' }}</p>
          </div>
        </div>

        <!-- comuni raggiunti -->
        <section aria-labelledby="titolo-comuni">
          <h3 id="titolo-comuni" class="etichetta mb-1.5 flex items-center justify-between px-1">
            <span>Comuni coinvolti</span>
            <span v-if="dati && !caricamento" class="cifre normal-case tracking-normal">{{ altri === 0 ? 'nessun altro comune' : altri === 1 ? '1 altro comune' : `${altri} altri comuni` }} entro +{{ cursore }} h</span>
          </h3>
          <ul v-if="caricamento" class="space-y-1"><li v-for="i in 3" :key="i" class="scheletro h-9 rounded-m" /></ul>
          <p v-else-if="!comuni.length" class="flex items-center gap-2 rounded-m px-3 py-2 text-[.8rem] text-testo-2"><Building2 class="size-4 shrink-0 text-testo-3" aria-hidden="true" />Nessun comune raggiunto nell'orizzonte scelto</p>
          <ul v-else class="space-y-1">
            <li v-for="c in comuni" :key="c.nome" class="flex h-9 items-center gap-2.5 rounded-m px-3 text-[.82rem] transition-colors duration-200" :class="c.raggiunto_ora <= cursore ? 'bg-brace/10 text-testo ring-1 ring-brace/25' : 'text-testo-3'">
              <span class="size-2 shrink-0 rounded-full transition-colors duration-200" :class="c.raggiunto_ora <= cursore ? 'bg-brace' : 'ring-[1.5px] ring-testo-3'" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate" :class="c.raggiunto_ora <= cursore && 'font-semibold'">{{ nomeComune(c.nome) }}</span>
              <span v-if="c.nome === origine" class="shrink-0 rounded-full bg-brace/15 px-2 py-px text-[.68rem] font-medium text-brace">origine</span>
              <span v-else class="cifre shrink-0 text-[.74rem]" :class="c.raggiunto_ora <= cursore ? 'text-brace' : ''">+{{ c.raggiunto_ora }} h</span>
              <span class="sr-only">{{ c.raggiunto_ora <= cursore ? 'raggiunto' : 'non ancora' }}</span>
            </li>
          </ul>
        </section>

        <!-- acqua piu' vicina al fronte finale -->
        <section v-if="caricamento || dati" aria-labelledby="titolo-acqua">
          <h3 id="titolo-acqua" class="etichetta mb-1.5 px-1">Acqua più vicina al fronte</h3>
          <ul v-if="caricamento" class="space-y-1"><li v-for="i in 2" :key="i" class="scheletro h-9 rounded-m" /></ul>
          <p v-else-if="!dati!.acqua.length" class="flex items-center gap-2 rounded-m px-3 py-2 text-[.8rem] text-testo-2"><Droplet class="size-4 shrink-0 text-testo-3" aria-hidden="true" />Nessuna fonte d'acqua nota: né invasi entro 40 km né punti segnalati entro 25 km</p>
          <template v-else>
            <ul v-if="invasi.length" class="space-y-1">
              <li v-for="(a, i) in invasi" :key="i">
                <button type="button" class="flex w-full items-center gap-2.5 rounded-m px-3 py-1.5 text-left text-[.82rem] transition-colors hover:bg-vetro-forte" :class="telefono ? 'min-h-11' : 'min-h-9'" @click="emit('vai', a.lon, a.lat)">
                  <Waves class="size-4 shrink-0 text-cielo" aria-hidden="true" />
                  <span class="min-w-0 flex-1">
                    <span class="block truncate font-medium">{{ a.nome }}</span>
                    <span v-if="a.riempimento != null" class="mt-1 flex items-center gap-1.5">
                      <span class="h-1 flex-1 overflow-hidden rounded-full bg-vetro-forte" aria-hidden="true"><span class="block h-full rounded-full bg-cielo" :style="{ width: `${Math.min(100, a.riempimento)}%` }" /></span>
                      <span class="cifre text-[.7rem] text-testo-2">{{ a.riempimento }}%<span class="sr-only"> di riempimento</span></span>
                    </span>
                  </span>
                  <span class="cifre shrink-0 text-[.74rem] text-testo-2">{{ a.distanza_km.toLocaleString('it-IT') }} km</span>
                </button>
              </li>
            </ul>
            <p v-else class="flex items-center gap-2 px-3 py-1.5 text-[.76rem] text-testo-3"><Waves class="size-4 shrink-0" aria-hidden="true" />Nessun invaso entro 40 km</p>
            <div v-if="puntiAcqua.length" class="mt-1">
              <button type="button" class="flex w-full items-center gap-2.5 rounded-m px-3 py-1.5 text-left text-[.8rem] text-testo-2 transition-colors hover:bg-vetro-forte" :class="telefono ? 'min-h-11' : 'min-h-9'" :aria-expanded="apriPunti" @click="apriPunti = !apriPunti">
                <Droplet class="size-4 shrink-0 text-cielo" aria-hidden="true" />
                <span class="min-w-0 flex-1"><span class="cifre">{{ puntiAcqua.length }}</span> {{ puntiAcqua.length === 1 ? "punto d'acqua segnalato" : "punti d'acqua segnalati" }} dai cittadini · il più vicino a <span class="cifre">{{ Math.min(...puntiAcqua.map((p) => p.distanza_km)).toLocaleString('it-IT') }} km</span></span>
                <ChevronDown class="size-4 shrink-0 text-testo-3 transition-transform" :class="apriPunti && 'rotate-180'" aria-hidden="true" />
              </button>
              <ul v-if="apriPunti" class="mt-1 space-y-0.5 pl-6">
                <li v-for="(p, i) in [...puntiAcqua].sort((x, y) => x.distanza_km - y.distanza_km)" :key="i">
                  <button type="button" class="flex w-full items-center gap-2 rounded-m px-3 text-left text-[.78rem] text-testo-2 transition-colors hover:bg-vetro-forte hover:text-testo" :class="telefono ? 'min-h-11' : 'min-h-8'" @click="emit('vai', p.lon, p.lat)">
                    <span class="min-w-0 flex-1 truncate">Punto {{ i + 1 }}</span>
                    <span class="cifre shrink-0 text-[.72rem]">{{ p.distanza_km.toLocaleString('it-IT') }} km</span>
                    <MapPin class="size-3.5 shrink-0 text-testo-3" aria-hidden="true" />
                  </button>
                </li>
              </ul>
            </div>
          </template>
        </section>
      </template>

      <!-- nota di onesta': sempre visibile -->
      <p class="flex gap-2 rounded-m border border-bordo px-3 py-2.5 text-[.72rem] leading-snug text-testo-2" :class="telefono && 'mb-1'">
        <Info class="mt-px size-3.5 shrink-0 text-testo-3" aria-hidden="true" />
        <span>Scenario indicativo: modello semplificato senza pendenza del terreno né intervento dei mezzi.<span v-if="notaMeteo" class="mt-1 block text-ambra">{{ notaMeteo }}</span></span>
      </p>
      <button v-if="telefono" type="button" class="secondario flex h-11 w-full items-center justify-center gap-1.5 text-sm" @click="emit('chiudi')"><X class="size-4" aria-hidden="true" />Chiudi scenario</button>
    </div>

    <footer v-if="!telefono" class="shrink-0 border-t border-bordo px-5 py-3.5">
      <button type="button" class="secondario flex h-10 w-full items-center justify-center gap-1.5 text-sm" @click="emit('chiudi')"><X class="size-4" aria-hidden="true" />Chiudi scenario</button>
    </footer>
  </div>
</template>

<style>
/* cursore temporale: traccia sottile, riempimento brace fino al pollice */
.cursore-scenario { appearance: none; height: 22px; background: transparent; cursor: pointer; }
.cursore-scenario:disabled { cursor: default; opacity: .5; }
.cursore-scenario::-webkit-slider-runnable-track { height: 4px; border-radius: 999px; background: linear-gradient(90deg, var(--ambra), var(--brace)) 0 0 / calc(var(--p, 0) * 100%) 100% no-repeat, var(--vetro-forte); }
.cursore-scenario::-moz-range-track { height: 4px; border-radius: 999px; background: var(--vetro-forte); }
.cursore-scenario::-moz-range-progress { height: 4px; border-radius: 999px; background: linear-gradient(90deg, var(--ambra), var(--brace)); }
.cursore-scenario::-webkit-slider-thumb { appearance: none; width: 18px; height: 18px; margin-top: -7px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 3px var(--brace), 0 2px 6px rgba(0,0,0,.35); }
.cursore-scenario::-moz-range-thumb { width: 18px; height: 18px; border: 0; border-radius: 999px; background: #fff; box-shadow: 0 0 0 3px var(--brace), 0 2px 6px rgba(0,0,0,.35); }
.cursore-scenario:focus-visible { outline: none; }
.cursore-scenario:focus-visible::-webkit-slider-thumb { box-shadow: 0 0 0 3px var(--brace), 0 0 0 6px var(--cielo); }
</style>
