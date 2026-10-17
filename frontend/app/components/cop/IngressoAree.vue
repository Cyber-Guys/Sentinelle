<script setup lang="ts">
import { ChevronRight, Flame, Siren } from '@lucide/vue'
import { LIVELLI_CFD, fmtGiorno, type AreaCop, type Bollettino } from '~/composables/useCop'

const props = defineProps<{ aree: AreaCop[]; hover: string | null; oggi: Bollettino | null; domani: Bollettino | null; incendi: Record<string, number>; segnalazioni: Record<string, number> }>()
defineEmits<{ scegli: [id: string]; hover: [id: string | null] }>()

const rossiDomani = computed(() => props.aree.filter((a) => props.domani?.per_area[a.id]?.massimo === 'rosso').map((a) => a.nome))
</script>

<template>
  <section class="ingresso sospeso flex w-[400px] max-w-[calc(100vw-32px)] flex-col overflow-hidden p-3" aria-labelledby="t-ingresso">
    <header class="px-2 pt-2 pb-3">
      <h1 id="t-ingresso" class="text-[1.3rem] leading-tight font-semibold tracking-[-0.01em]">Scegli l'area di competenza</h1>
      <p class="mt-1 text-[.82rem] text-testo-2">Sette Centri Operativi Provinciali coprono la Sardegna. Bollettino CFD di {{ oggi ? fmtGiorno(oggi.valido_per) : 'oggi' }}.</p>
    </header>
    <ul class="cop-scroll -mx-0.5 flex min-h-0 flex-col gap-1 overflow-y-auto px-0.5" @mouseleave="$emit('hover', null)">
      <li v-for="(a, k) in aree" :key="a.id" class="voce" :style="{ '--i': k }">
        <button type="button" class="riga flex w-full items-center gap-3 rounded-m px-3 py-2.5 text-left" :class="{ sopra: hover === a.id }"
          @mouseenter="$emit('hover', a.id)" @focus="$emit('hover', a.id)" @click="$emit('scegli', a.id)">
          <span class="livello size-2.5 shrink-0 rounded-full" :style="{ background: oggi ? LIVELLI_CFD[oggi.per_area[a.id]?.massimo ?? 'verde'].css : 'var(--bordo-luce)' }" aria-hidden="true" />
          <span class="min-w-0 flex-1">
            <span class="block text-[.94rem] font-semibold">{{ a.nome }}</span>
            <span class="mt-0.5 flex items-center gap-2.5 text-[.74rem] text-testo-3">
              <span v-if="oggi" :style="{ color: LIVELLI_CFD[oggi.per_area[a.id]?.massimo ?? 'verde'].css }">{{ LIVELLI_CFD[oggi.per_area[a.id]?.massimo ?? 'verde'].etichetta }}</span>
              <span class="cifre">{{ a.comuni }} comuni</span>
            </span>
          </span>
          <span class="flex items-center gap-2.5 text-[.76rem]">
            <span v-if="incendi[a.id]" class="cifre flex items-center gap-1 text-brace" :title="`${incendi[a.id]} incendi attivi`"><Flame class="size-3.5" aria-hidden="true" />{{ incendi[a.id] }}</span>
            <span v-if="segnalazioni[a.id]" class="cifre flex items-center gap-1 text-ambra" :title="`${segnalazioni[a.id]} segnalazioni da verificare`"><Siren class="size-3.5" aria-hidden="true" />{{ segnalazioni[a.id] }}</span>
          </span>
          <ChevronRight class="freccia size-4 shrink-0 text-testo-3" aria-hidden="true" />
        </button>
      </li>
    </ul>
    <p v-if="rossiDomani.length" class="mx-2 mt-3 border-t border-bordo pt-3 text-[.78rem] text-testo-2">
      Domani pericolo alto a <span class="font-medium text-testo">{{ rossiDomani.join(', ') }}</span>.
    </p>
  </section>
</template>

<style scoped>
.voce { animation: entra 460ms var(--ease-out) both; animation-delay: calc(120ms + var(--i) * 40ms); }
@keyframes entra { from { opacity: 0; transform: translateX(-8px); } }
.riga { transition: background-color 150ms ease; }
.riga.sopra, .riga:focus-visible { background: var(--vetro-forte); }
.freccia { transition: transform 200ms var(--ease-out), color 150ms ease; }
.riga.sopra .freccia { transform: translateX(2px); color: var(--testo); }
.livello { transition: scale 200ms var(--ease-out); }
.riga.sopra .livello { scale: 1.25; }
</style>
