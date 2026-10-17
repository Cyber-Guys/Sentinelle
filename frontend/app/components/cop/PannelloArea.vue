<script setup lang="ts">
import { Flame, ChevronRight, Siren, Droplets, FlameKindling } from '@lucide/vue'
import BarraAllerta from './BarraAllerta.vue'
import GraficoMesi from './GraficoMesi.vue'
import { LIVELLI_CFD, MEZZO_LIBERO, distanzaKm, stimaArrivo, fmtOre, fmtNum, fmtPct, type AreaCop, type Bollettino, type Incendio, type Statistiche } from '~/composables/useCop'

const props = defineProps<{
  area: AreaCop; bollettino: Bollettino | null; giorno: 'oggi' | 'domani'; incendi: Incendio[]; daVerificare: number
  flotta: any[]; flottaArea: any[]; invasi: any[]; fuochi: any[]; statistiche: Statistiche | null; ora: number
}>()
defineEmits<{ incendio: [id: string]; segnalazioni: [] }>()

const quote = computed(() => props.bollettino?.per_area[props.area.id] ?? null)
const frase = computed(() => {
  const q = quote.value
  if (!q) return ''
  const quando = props.giorno === 'oggi' ? 'Oggi' : 'Domani'
  if (q.rosso > 0.01) return `${quando} pericolo alto sul ${fmtPct(q.rosso)} dell'area.`
  if (q.arancione > 0.01) return `${quando} pericolo medio sul ${fmtPct(q.arancione)} dell'area, nessuna zona rossa.`
  return `${quando} pericolo basso su tutta l'area.`
})
const emesso = computed(() => props.bollettino ? new Date(props.bollettino.emesso_il).toLocaleString('it-IT', { weekday: 'long', hour: '2-digit', minute: '2-digit' }) : '')

const attivi = computed(() => props.incendi.filter((i) => i.stato === 'attivo'))
const ettariAttivi = computed(() => attivi.value.reduce((s, i) => s + i.ettari, 0))
const libero = (m: any) => MEZZO_LIBERO.includes(m.stato)
const terraArea = computed(() => props.flottaArea.filter((m) => m.categoria === 'terra'))
const aerei = computed(() => props.flotta.filter((m) => m.categoria === 'aereo'))
const acquaMedia = computed(() => {
  const l = props.invasi.filter((f) => f.properties.capacita_mm3 > 0)
  const cap = l.reduce((s, f) => s + f.properties.capacita_mm3, 0)
  return cap ? l.reduce((s, f) => s + f.properties.volume_mm3, 0) / cap : 0
})

// mezzo libero piu' vicino a ogni incendio attivo (terra o aria, tempo stimato)
function piuVicino(i: Incendio) {
  return props.flotta.filter(libero).map((m) => ({ m, km: distanzaKm(i.centro, [m.lon, m.lat]) }))
    .map((x) => ({ ...x, min: stimaArrivo(x.km, x.m) })).sort((a, b) => a.min - b.min)[0]
}

// mezzi per stato: liberi, in missione (in viaggio / acqua), sul posto
const GRUPPI = [
  { id: 'liberi', etichetta: 'Liberi', css: 'var(--macchia)', stati: MEZZO_LIBERO },
  { id: 'missione', etichetta: 'In missione', css: 'var(--cielo)', stati: ['In movimento', 'In volo', 'Carico acqua'] },
  { id: 'posto', etichetta: 'Sul posto', css: 'var(--brace)', stati: ['Sul posto', 'Lancio'] },
]
const ripartizione = (l: any[]) => GRUPPI.map((g) => ({ ...g, n: l.filter((m) => g.stati.includes(m.stato)).length }))
const righeMezzi = computed(() => [
  { titolo: "Terrestri nell'area", tot: terraArea.value.length, parti: ripartizione(terraArea.value) },
  { titolo: 'Aerei (flotta regionale)', tot: aerei.value.length, parti: ripartizione(aerei.value) },
])

const invasiOrdinati = computed(() => [...props.invasi].sort((a, b) => b.properties.capacita_mm3 - a.properties.capacita_mm3).slice(0, 4))
const fuochiInCorso = computed(() => props.fuochi.filter((f) => f.properties.stato === 'In corso'))
const fuochiProgr = computed(() => props.fuochi.filter((f) => f.properties.stato === 'Programmato').length)
const media2025 = computed(() => {
  const s = props.statistiche
  if (!s) return null
  const a = s.mesi_2025.reduce((x, y) => x + y, 0), m = s.mesi_media.reduce((x, y) => x + y, 0)
  return m ? (a - m) / m : null
})

const nIncendi = useConteggio(() => attivi.value.length)
const nVerifica = useConteggio(() => props.daVerificare)
const nLiberi = useConteggio(() => terraArea.value.filter(libero).length)
const nAcqua = useConteggio(() => Math.round(acquaMedia.value * 100))
</script>

<template>
  <div class="flex flex-col gap-3 pb-4">
    <header class="sezione px-1 pt-1" style="--i: 0">
      <h2 class="text-[1.35rem] leading-tight font-semibold tracking-[-0.01em]">COP {{ area.nome }}</h2>
      <p class="mt-0.5 text-[.8rem] text-testo-3">{{ area.comuni }} comuni · Centro Operativo Provinciale</p>
    </header>

    <!-- Bollettino CFD dell'area -->
    <section v-if="quote" class="sezione vetro p-3.5" style="--i: 1" aria-labelledby="t-cfd">
      <div class="flex items-baseline justify-between gap-2">
        <h3 id="t-cfd" class="text-[.86rem] font-semibold">Bollettino CFD</h3>
        <span class="text-[.72rem] text-testo-3">simulato</span>
      </div>
      <p class="mt-1 text-[.84rem] leading-snug text-testo-2">
        <span class="font-medium" :style="{ color: LIVELLI_CFD[quote.massimo].css }">{{ LIVELLI_CFD[quote.massimo].breve }}</span> · {{ frase }}
      </p>
      <BarraAllerta class="mt-3" :quote="quote" />
      <p class="mt-2.5 text-[.72rem] text-testo-3">Emesso {{ emesso }} dal Centro Funzionale Decentrato</p>
    </section>

    <!-- Situazione: quattro cifre, una riga -->
    <section class="sezione vetro grid grid-cols-2 gap-px overflow-hidden p-0" style="--i: 2" aria-label="Situazione dell'area">
      <div class="cella">
        <p class="cifre flex items-center gap-2 text-[1.5rem] leading-none font-semibold"><span v-if="attivi.length" class="punto-vivo punto-brace" />{{ nIncendi }}</p>
        <p class="mt-1.5 text-[.76rem] text-testo-2">Incendi attivi</p>
        <p class="cifre text-[.72rem] text-testo-3">{{ fmtNum(ettariAttivi) }} ha percorsi</p>
      </div>
      <button type="button" class="cella cella-azione text-left" @click="$emit('segnalazioni')">
        <p class="cifre text-[1.5rem] leading-none font-semibold" :class="{ 'text-ambra': daVerificare }">{{ nVerifica }}</p>
        <p class="mt-1.5 flex items-center gap-1 text-[.76rem] text-testo-2">Da verificare <ChevronRight class="size-3.5 text-testo-3" aria-hidden="true" /></p>
        <p class="text-[.72rem] text-testo-3">segnalazioni dei cittadini</p>
      </button>
      <div class="cella">
        <p class="cifre text-[1.5rem] leading-none font-semibold">{{ nLiberi }}<span class="text-[.95rem] font-medium text-testo-3">/{{ terraArea.length }}</span></p>
        <p class="mt-1.5 text-[.76rem] text-testo-2">Mezzi di terra liberi</p>
        <p class="cifre text-[.72rem] text-testo-3">{{ aerei.filter(libero).length }} aerei liberi in regione</p>
      </div>
      <div class="cella">
        <p class="cifre text-[1.5rem] leading-none font-semibold">{{ nAcqua }}<span class="text-[.95rem] font-medium text-testo-3">%</span></p>
        <p class="mt-1.5 text-[.76rem] text-testo-2">Riserva idrica</p>
        <p class="cifre text-[.72rem] text-testo-3">{{ invasi.length }} invasi nell'area</p>
      </div>
    </section>

    <!-- Incendi attivi -->
    <section class="sezione vetro p-1.5" style="--i: 3" aria-labelledby="t-inc">
      <h3 id="t-inc" class="px-2 pt-1.5 pb-1 text-[.86rem] font-semibold">Incendi in corso</h3>
      <p v-if="!attivi.length" class="px-2 pb-2 text-[.8rem] text-testo-3">Nessun incendio attivo nell'area.</p>
      <button v-for="i in attivi" :key="i.id" type="button" class="riga flex w-full items-center gap-3 rounded-m px-2 py-2 text-left" @click="$emit('incendio', i.id)">
        <span class="flex size-8 shrink-0 items-center justify-center rounded-s bg-brace/15 text-brace"><Flame class="size-4" aria-hidden="true" /></span>
        <span class="min-w-0 flex-1">
          <span class="block truncate text-[.84rem] font-medium">{{ i.nome }}</span>
          <span class="cifre block truncate text-[.74rem] text-testo-3">da {{ fmtOre(i.inizio, ora) }} · {{ fmtNum(i.ettari) }} ha
            <template v-if="piuVicino(i)"> · {{ piuVicino(i)!.m.sigla }} a {{ piuVicino(i)!.min }} min</template>
          </span>
        </span>
        <ChevronRight class="size-4 shrink-0 text-testo-3" aria-hidden="true" />
      </button>
    </section>

    <!-- Mezzi -->
    <section class="sezione vetro p-3.5" style="--i: 4" aria-labelledby="t-mezzi">
      <div class="flex items-baseline justify-between">
        <h3 id="t-mezzi" class="text-[.86rem] font-semibold">Disponibilità mezzi</h3>
        <span class="text-[.72rem] text-testo-3">flotta simulata</span>
      </div>
      <div v-for="r in righeMezzi" :key="r.titolo" class="mt-3">
        <div class="flex justify-between text-[.76rem]"><span class="text-testo-2">{{ r.titolo }}</span><span class="cifre text-testo-3">{{ r.tot }}</span></div>
        <div class="mt-1.5 flex h-2 gap-[2px] overflow-hidden rounded-full bg-vetro">
          <div v-for="p in r.parti.filter((x) => x.n)" :key="p.id" class="parte h-full" :style="{ flexGrow: p.n, background: p.css }" :title="`${p.etichetta}: ${p.n}`" />
        </div>
      </div>
      <div class="mt-2.5 flex gap-3.5 text-[.72rem] text-testo-2">
        <span v-for="g in GRUPPI" :key="g.id" class="flex items-center gap-1.5"><span class="size-2 rounded-full" :style="{ background: g.css }" />{{ g.etichetta }}</span>
      </div>
    </section>

    <!-- Storico mensile -->
    <section class="sezione vetro p-3.5" style="--i: 5" aria-labelledby="t-mesi">
      <div class="flex items-baseline justify-between gap-2">
        <h3 id="t-mesi" class="text-[.86rem] font-semibold">Incendi per mese</h3>
        <span v-if="media2025 != null" class="cifre text-[.72rem]" :class="media2025 > 0 ? 'text-brace' : 'text-macchia'">{{ media2025 > 0 ? '+' : '' }}{{ fmtPct(media2025) }} sulla media</span>
      </div>
      <GraficoMesi v-if="statistiche" class="mt-2" :anno="statistiche.mesi_2025" :media="statistiche.mesi_media" />
      <div v-else class="scheletro mt-3 h-[150px] rounded-m" />
      <p class="mt-1.5 text-[.72rem] text-testo-3">Perimetri CFVA nell'area, 2015-2025</p>
    </section>

    <!-- Riserve d'acqua -->
    <section class="sezione vetro p-3.5" style="--i: 6" aria-labelledby="t-acqua">
      <h3 id="t-acqua" class="text-[.86rem] font-semibold">Riserve d'acqua</h3>
      <p v-if="!invasi.length" class="mt-1 text-[.8rem] text-testo-3">Nessun invaso censito nell'area.</p>
      <ul class="mt-2 flex flex-col gap-2.5">
        <li v-for="f in invasiOrdinati" :key="f.properties.nome" class="flex items-center gap-3">
          <Droplets class="size-4 shrink-0 text-cielo" aria-hidden="true" />
          <span class="min-w-0 flex-1">
            <span class="flex justify-between gap-2 text-[.8rem]"><span class="truncate">{{ f.properties.nome }}</span><span class="cifre text-testo-2">{{ f.properties.riempimento }}%</span></span>
            <span class="mt-1 block h-1.5 overflow-hidden rounded-full bg-vetro-forte"><span class="block h-full rounded-full bg-cielo" :style="{ width: `${f.properties.riempimento}%` }" /></span>
            <span class="cifre mt-0.5 block text-[.7rem] text-testo-3">{{ fmtNum(f.properties.volume_mm3, 1) }} di {{ fmtNum(f.properties.capacita_mm3, 1) }} milioni di m³</span>
          </span>
        </li>
      </ul>
    </section>

    <!-- Fuochi autorizzati -->
    <section class="sezione vetro p-3.5" style="--i: 7" aria-labelledby="t-fuochi">
      <div class="flex items-baseline justify-between">
        <h3 id="t-fuochi" class="text-[.86rem] font-semibold">Fuochi autorizzati oggi</h3>
        <span class="cifre text-[.72rem] text-testo-3">{{ fuochi.length }} permessi</span>
      </div>
      <p class="mt-1 text-[.8rem] text-testo-2">
        <span class="cifre font-medium text-testo">{{ fuochiInCorso.length }}</span> in corso, <span class="cifre font-medium text-testo">{{ fuochiProgr }}</span> programmati.
        Un fumo segnalato vicino a un fuoco autorizzato va verificato prima di allertare.
      </p>
      <ul v-if="fuochiInCorso.length" class="mt-2 flex flex-col gap-1.5">
        <li v-for="f in fuochiInCorso" :key="f.properties.id" class="flex items-center gap-2.5 text-[.78rem]">
          <FlameKindling class="size-3.5 shrink-0 text-viola" aria-hidden="true" />
          <span class="min-w-0 flex-1 truncate">{{ f.properties.comune }} · {{ f.properties.tipo.toLowerCase() }}</span>
          <span class="cifre text-testo-3">{{ f.properties.dalle }}-{{ f.properties.alle }}</span>
        </li>
      </ul>
    </section>

    <p class="sezione px-1 text-[.7rem] leading-relaxed text-testo-3" style="--i: 8">
      <Siren class="mr-1 inline size-3 align-[-1px]" aria-hidden="true" />Simulati per la demo: bollettino CFD, vedette, fuochi autorizzati, flotta e incendi dimostrativi. Reali: comuni, basi, invasi, storico CFVA.
    </p>
  </div>
</template>

<style scoped>
/* ingresso a cascata quando cambia l'area (il pannello e' montato con :key = area) */
.sezione { animation: sale 420ms var(--ease-out) both; animation-delay: calc(var(--i) * 45ms); }
@keyframes sale { from { opacity: 0; transform: translateY(10px); } }
.cella { background: var(--vetro); padding: 12px 14px; }
.cella-azione { transition: background-color 150ms ease; }
@media (hover: hover) { .cella-azione:hover, .riga:hover { background: var(--vetro-forte); } }
.riga { transition: background-color 150ms ease; }
.parte { flex-basis: 0; transition: flex-grow 600ms var(--ease-in-out); }
.punto-brace { --pin: var(--brace); }
</style>
