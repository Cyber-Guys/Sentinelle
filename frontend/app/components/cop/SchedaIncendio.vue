<script setup lang="ts">
import { ArrowLeft, Truck, Plane, Droplets, Binoculars, CircleCheck, Flame, Clock3 } from '@lucide/vue'
import { MEZZO_LIBERO, distanzaKm, stimaArrivo, fmtOre, fmtNum, type Incendio } from '~/composables/useCop'

const props = defineProps<{ incendio: Incendio; area: string; flotta: any[]; invasi: any[]; vedette: any[]; ora: number; oreAreaSpenta: number; inCorso: boolean }>()
const emit = defineEmits<{ indietro: []; concludi: [id: string] }>()

const i = computed(() => props.incendio)
const attivo = computed(() => i.value.stato === 'attivo')
const ora = (iso: string | null) => (iso ? new Date(iso).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) : '')

const mezzi = computed(() => props.flotta.filter((m) => MEZZO_LIBERO.includes(m.stato))
  .map((m) => { const km = distanzaKm(i.value.centro, [m.lon, m.lat]); return { m, km, min: stimaArrivo(km, m) } })
  .sort((a, b) => a.min - b.min).slice(0, 4))
const impegnati = computed(() => props.flotta.filter((m) => !MEZZO_LIBERO.includes(m.stato) && distanzaKm(i.value.centro, [m.lon, m.lat]) < 6))
const acqua = computed(() => props.invasi.map((f) => ({ f, km: distanzaKm(i.value.centro, f.geometry.coordinates) })).sort((a, b) => a.km - b.km).slice(0, 3))
const vedette = computed(() => props.vedette.filter((f) => distanzaKm(i.value.centro, f.geometry.coordinates) <= f.properties.raggio_km))
const restano = computed(() => {
  if (!i.value.spento_il) return 0
  return Math.max(0, Math.round(props.oreAreaSpenta - (props.ora - new Date(i.value.spento_il).getTime()) / 3.6e6))
})

const conferma = ref(false)
watch(() => props.incendio.id, () => (conferma.value = false))
</script>

<template>
  <div class="flex flex-col gap-3 pb-4">
    <button type="button" class="indietro -ml-1 flex h-8 w-fit items-center gap-1.5 rounded-full pr-3 pl-2 text-[.8rem] text-testo-2" @click="emit('indietro')">
      <ArrowLeft class="size-4" aria-hidden="true" /> COP {{ area }}
    </button>

    <header class="px-1">
      <p class="flex items-center gap-2 text-[.78rem] font-medium" :class="attivo ? 'text-brace' : 'text-testo-3'">
        <span v-if="attivo" class="punto-vivo punto-brace" /><CircleCheck v-else class="size-3.5" aria-hidden="true" />
        {{ attivo ? 'Incendio attivo' : 'Spento' }}
      </p>
      <h2 class="mt-1 text-[1.3rem] leading-tight font-semibold tracking-[-0.01em]">{{ i.nome }}</h2>
      <p class="mt-0.5 text-[.8rem] text-testo-3">{{ i.comune }} · {{ i.origine === 'segnalazione' ? `segnalazione #${i.segnalazione_id} certificata` : 'scenario dimostrativo' }}</p>
    </header>

    <dl class="vetro grid grid-cols-3 gap-px overflow-hidden p-0">
      <div class="cella"><dt class="text-[.72rem] text-testo-3">Innesco</dt><dd class="cifre m-0 mt-1 text-[1.05rem] font-semibold">{{ ora(i.inizio) }}</dd><dd class="cifre m-0 text-[.7rem] text-testo-3">{{ fmtOre(i.inizio, props.ora) }} fa</dd></div>
      <div class="cella"><dt class="text-[.72rem] text-testo-3">Superficie</dt><dd class="cifre m-0 mt-1 text-[1.05rem] font-semibold">{{ fmtNum(i.ettari) }} ha</dd><dd class="m-0 text-[.7rem] text-testo-3">stimata</dd></div>
      <div class="cella"><dt class="text-[.72rem] text-testo-3">Fronte</dt><dd class="cifre m-0 mt-1 text-[1.05rem] font-semibold">{{ attivo ? `${fmtNum(i.fronte_m / 1000, 1)} km` : '-' }}</dd><dd class="m-0 text-[.7rem] text-testo-3">{{ attivo ? 'lineare' : 'chiuso' }}</dd></div>
    </dl>

    <template v-if="attivo">
      <section class="vetro p-1.5" aria-labelledby="t-mezzi-vicini">
        <h3 id="t-mezzi-vicini" class="px-2 pt-1.5 pb-1 text-[.86rem] font-semibold">Mezzi liberi più vicini</h3>
        <ul>
          <li v-for="x in mezzi" :key="x.m.id" class="flex items-center gap-3 rounded-m px-2 py-1.5">
            <span class="flex size-8 shrink-0 items-center justify-center rounded-s bg-vetro-forte text-testo-2">
              <component :is="x.m.categoria === 'aereo' ? Plane : Truck" class="size-4" aria-hidden="true" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-[.82rem] font-medium">{{ x.m.sigla }}</span>
              <span class="block truncate text-[.72rem] text-testo-3">{{ x.m.tipo }} · {{ x.m.stato.toLowerCase() }}</span>
            </span>
            <span class="text-right">
              <span class="cifre block text-[.86rem] font-semibold">{{ x.min }} min</span>
              <span class="cifre block text-[.7rem] text-testo-3">{{ fmtNum(x.km, 1) }} km</span>
            </span>
          </li>
        </ul>
        <p v-if="impegnati.length" class="px-2 pt-1 pb-1.5 text-[.74rem] text-testo-3">
          <Flame class="mr-1 inline size-3 align-[-1px] text-brace" aria-hidden="true" />Già in zona: {{ impegnati.map((m) => m.sigla).join(', ') }}
        </p>
      </section>

      <section class="vetro p-3.5" aria-labelledby="t-acqua-vicina">
        <h3 id="t-acqua-vicina" class="text-[.86rem] font-semibold">Acqua per i mezzi aerei</h3>
        <ul class="mt-2 flex flex-col gap-2">
          <li v-for="a in acqua" :key="a.f.properties.nome" class="flex items-center gap-2.5 text-[.8rem]">
            <Droplets class="size-4 shrink-0 text-cielo" aria-hidden="true" />
            <span class="min-w-0 flex-1 truncate">{{ a.f.properties.nome }}</span>
            <span class="cifre text-testo-2">{{ a.f.properties.riempimento }}%</span>
            <span class="cifre w-14 text-right text-testo-3">{{ fmtNum(a.km, 1) }} km</span>
          </li>
        </ul>
      </section>

      <section class="vetro p-3.5" aria-labelledby="t-vedette">
        <h3 id="t-vedette" class="text-[.86rem] font-semibold">Vedette che coprono l'area</h3>
        <p v-if="!vedette.length" class="mt-1 text-[.8rem] text-testo-3">Nessuna vedetta ha l'incendio nel proprio raggio.</p>
        <ul v-else class="mt-2 flex flex-col gap-1.5">
          <li v-for="v in vedette" :key="v.properties.id" class="flex items-center gap-2.5 text-[.8rem]">
            <Binoculars class="size-4 shrink-0 text-cielo" aria-hidden="true" />
            <span class="min-w-0 flex-1 truncate">{{ v.properties.nome }}</span>
            <span class="text-[.74rem]" :class="v.properties.stato === 'Presidiata' ? 'text-macchia' : 'text-testo-3'">{{ v.properties.stato }}</span>
          </li>
        </ul>
      </section>

      <!-- chiusura: conferma in linea, niente modale -->
      <div class="mt-1">
        <Transition name="scambio" mode="out-in">
          <button v-if="!conferma" key="a" type="button" class="secondario flex h-11 w-full items-center justify-center gap-2 text-[.88rem]" @click="conferma = true">
            <CircleCheck class="size-4" aria-hidden="true" /> Segna come concluso
          </button>
          <div v-else key="b" class="vetro p-3">
            <p class="text-[.82rem] leading-snug">Le squadre hanno finito? L'incendio sparisce dall'app dei cittadini e l'area bruciata resta segnata come spenta per {{ oreAreaSpenta }} ore.</p>
            <div class="mt-3 flex gap-2">
              <button type="button" class="secondario h-10 flex-1 text-[.84rem]" @click="conferma = false">Annulla</button>
              <button type="button" class="primario h-10 flex-[1.4] text-[.84rem]" :disabled="inCorso" @click="emit('concludi', i.id)">{{ inCorso ? 'Chiusura...' : 'Conferma chiusura' }}</button>
            </div>
          </div>
        </Transition>
      </div>
    </template>

    <section v-else class="vetro p-3.5">
      <p class="flex items-center gap-2 text-[.84rem] font-medium"><Clock3 class="size-4 text-testo-3" aria-hidden="true" />Spento alle {{ ora(i.spento_il) }}</p>
      <p class="mt-1 text-[.8rem] text-testo-2">L'area bruciata resta sulla mappa ancora per {{ restano }} ore, poi passa allo storico.</p>
    </section>
  </div>
</template>

<style scoped>
.cella { background: var(--vetro); padding: 10px 12px; }
.indietro { transition: background-color 150ms ease, color 150ms ease; }
@media (hover: hover) { .indietro:hover { background: var(--vetro-forte); color: var(--testo); } }
.punto-brace { --pin: var(--brace); }
.scambio-enter-active, .scambio-leave-active { transition: opacity 180ms ease, transform 220ms var(--ease-out), filter 180ms ease; }
.scambio-enter-from, .scambio-leave-to { opacity: 0; transform: translateY(4px); filter: blur(2px); }
</style>
