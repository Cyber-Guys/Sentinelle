<script setup lang="ts">
import { Gauge, TriangleAlert } from '@lucide/vue'
import type { GrigliaRischio } from '~/composables/useMappa'

// Sezione "Rischio di oggi" del pannello Livelli (app e cruscotto): interruttore, legenda macchia -> ambra -> brace, avviso meteo simulato.
defineProps<{ griglia: GrigliaRischio | null; caricamento?: boolean; errore?: boolean; grande?: boolean }>()
const acceso = defineModel<boolean>({ required: true })
const ora = (iso: string) => new Date(iso).toLocaleTimeString('it-IT', { timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit' })
</script>

<template>
  <div>
    <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
      <input v-model="acceso" type="checkbox" role="switch" class="sr-only" />
      <Gauge class="size-4 shrink-0 text-ambra" aria-hidden="true" />
      <span class="min-w-0 flex-1 leading-tight">
        <span class="block text-[.86rem] font-semibold">Rischio di oggi</span>
        <span class="block text-[.72rem] text-testo-2">Celle di 2 km: storico, vegetazione, meteo</span>
      </span>
      <span class="interruttore" :class="acceso && 'acceso'" aria-hidden="true" />
    </label>
    <div v-if="acceso" class="px-3 pt-1 pb-1 text-[.72rem]">
      <p v-if="errore" class="flex items-center gap-1.5 text-ambra"><TriangleAlert class="size-3.5 shrink-0" aria-hidden="true" />Rischio non disponibile, riprova tra poco</p>
      <template v-else>
        <div class="legenda-rischio h-1.5 rounded-full" :class="caricamento && 'animate-pulse'" aria-hidden="true" />
        <div class="mt-1 flex justify-between text-testo-3"><span>Basso</span><span>Medio</span><span>Alto</span></div>
        <p class="sr-only">Colore delle celle: verde per rischio basso, ambra medio, brace alto.</p>
        <p v-if="griglia" class="cifre mt-1.5 text-testo-3">Peggiori condizioni delle prossime 24 h · agg. {{ ora(griglia.aggiornato_il) }}</p>
        <p v-if="griglia?.meteo_simulato" class="mt-1.5 flex items-start gap-1.5 text-ambra"><TriangleAlert class="mt-px size-3.5 shrink-0" aria-hidden="true" />Meteo simulato: previsione non raggiungibile</p>
      </template>
    </div>
  </div>
</template>

<style>
.legenda-rischio { background: linear-gradient(90deg, #3fb37f, #f5b83d 50%, #ff6a2b); opacity: .85; }
html[data-tema='chiaro'] .legenda-rischio { background: linear-gradient(90deg, #2f8f63, #d99a1e 50%, #e8351f); }
</style>
