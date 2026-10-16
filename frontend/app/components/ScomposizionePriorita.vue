<script setup lang="ts">
// Priorita' come cifra + scala 0-100 con soglie, poi la scomposizione per fattore:
// una riga per termine con il contributo in punti (barre su scala comune, quindi confrontabili).
import { Satellite, Wind, Trees, TriangleAlert, Users, History, Info, ShieldCheck } from '@lucide/vue'
import type { Fattore } from '~/composables/useApi'

const props = defineProps<{ priorita: number; fattori?: Fattore[]; motivazioni?: string[] }>()

const ICONE: Record<string, any> = { hotspot: Satellite, meteo: Wind, suolo: Trees, pericolo: TriangleAlert, vicine: Users, storico: History, affidabilita: ShieldCheck }
const SOGLIE = [30, 60]

const colore = computed(() => varPriorita(props.priorita))
const fattori = computed(() => props.fattori ?? [])
// 100% della barra = il contributo massimo possibile del fattore piu' pesante
const scala = computed(() => Math.max(...fattori.value.map((f) => f.peso * 100), 1))
const mancanti = computed(() => fattori.value.some((f) => !f.disponibile))
const coloreFattore = (v: number) => (v >= 0.66 ? 'var(--brace)' : v >= 0.33 ? 'var(--ambra)' : 'var(--testo-3)')
const punti = (c: number) => (c > 0 && c < 1 ? '<1' : String(Math.round(c)))
</script>

<template>
  <div class="space-y-4">
    <!-- punteggio -->
    <div>
      <div class="flex items-end justify-between gap-3">
        <p class="flex items-baseline gap-1.5 leading-none">
          <span class="cifre text-[2.6rem] font-semibold tracking-tight" :style="{ color: colore }">{{ priorita }}</span>
          <span class="cifre text-sm text-testo-3">/ 100</span>
        </p>
        <p class="pb-1 text-right leading-tight">
          <span class="etichetta block">Priorità</span>
          <span class="text-[.95rem] font-semibold" :style="{ color: colore }">{{ etichettaPriorita(priorita) }}</span>
        </p>
      </div>
      <div class="relative mt-2.5" role="img" :aria-label="`Priorità ${priorita} su 100, soglie a 30 e 60`">
        <div class="flex h-1 gap-px overflow-hidden rounded-full">
          <span class="h-full bg-bassa/25" style="width: 30%" />
          <span class="h-full bg-media/25" style="width: 30%" />
          <span class="h-full flex-1 bg-alta/25" />
        </div>
        <div class="absolute inset-y-0 left-0 h-1 rounded-full" :style="{ width: `${Math.max(1, priorita)}%`, background: colore }" />
        <span class="absolute -top-[3px] h-2.5 w-0.5 rounded-full bg-testo" :style="{ left: `calc(${Math.min(99.5, priorita)}% - 1px)` }" aria-hidden="true" />
        <div class="cifre relative mt-1.5 h-3 text-[.62rem] text-testo-3" aria-hidden="true">
          <span class="absolute left-0">0</span>
          <span v-for="s in SOGLIE" :key="s" class="absolute -translate-x-1/2" :style="{ left: `${s}%` }">{{ s }}</span>
          <span class="absolute right-0">100</span>
        </div>
      </div>
    </div>

    <!-- scomposizione per fattore -->
    <div v-if="fattori.length">
      <div class="mb-1.5 flex items-baseline justify-between">
        <p class="etichetta">Scomposizione</p>
        <p class="etichetta">Punti</p>
      </div>
      <ul class="divide-y divide-bordo border-y border-bordo">
        <li v-for="f in fattori" :key="f.chiave" class="grid grid-cols-[1rem_1fr_2.25rem] gap-x-3 py-2.5" :class="!f.disponibile && 'opacity-60'">
          <component :is="ICONE[f.chiave] ?? Info" class="mt-px size-4 text-testo-3" aria-hidden="true" />
          <div class="min-w-0">
            <p class="text-[.84rem] font-medium leading-tight">{{ f.etichetta }}</p>
            <p class="mt-0.5 text-[.78rem] leading-snug text-testo-2">{{ f.disponibile ? f.testo : 'Non disponibile: peso ridistribuito sugli altri fattori' }}</p>
            <div v-if="f.disponibile" class="relative mt-1.5 h-1 rounded-full" aria-hidden="true">
              <span class="absolute inset-y-0 left-0 rounded-full bg-bordo-luce/70" :style="{ width: `${(f.peso * 100) / scala * 100}%` }" />
              <span class="absolute inset-y-0 left-0 rounded-full" :style="{ width: `${f.contributo / scala * 100}%`, background: coloreFattore(f.valore) }" />
            </div>
          </div>
          <p class="cifre text-right text-[.84rem] font-semibold leading-tight" :class="f.disponibile ? (f.contributo >= 0.5 ? 'text-testo' : 'text-testo-3') : 'text-testo-3'">
            <span v-if="f.disponibile" :aria-label="`${punti(f.contributo)} punti su ${Math.round(f.peso * 100)} possibili`">{{ punti(f.contributo) }}</span>
            <span v-else class="text-[.7rem] font-medium">n.d.</span>
          </p>
        </li>
      </ul>
      <p class="mt-2 text-[.72rem] leading-snug text-testo-3">
        La barra chiara è il massimo che il fattore può dare; quella colorata i punti apportati.<template v-if="mancanti"> Le fonti non disponibili sono escluse e i pesi ricalcolati.</template>
      </p>
    </div>

    <!-- segnalazioni precedenti alla scomposizione: solo le motivazioni -->
    <ul v-else-if="motivazioni?.length" class="divide-y divide-bordo border-y border-bordo text-[.82rem]">
      <li v-for="m in motivazioni" :key="m" class="py-2 text-testo-2">{{ m }}</li>
    </ul>
  </div>
</template>
