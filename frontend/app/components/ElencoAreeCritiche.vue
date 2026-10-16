<script setup lang="ts">
// Aree critiche di oggi (cruscotto: colonna su desktop, foglio su telefono).
// Riga = livello (colore + parola), nome, picco; la selezionata si apre con motivo, comuni, acqua, fattori e "Simula scenario".
import { Clock, Droplet, Play, History, TriangleAlert, Wind, Droplets, SunMedium, ChevronDown } from '@lucide/vue'

const props = defineProps<{ dati: AreeCritiche | null; caricamento: boolean; errore: boolean; selezionata: number | null }>()
const emit = defineEmits<{ seleziona: [a: AreaCritica]; simula: [a: AreaCritica]; riprova: [] }>()

const ICONE: Record<string, any> = { storico: History, pericolo: TriangleAlert, vento: Wind, umidita: Droplets, pioggia: SunMedium }
const coloreFattore = (v: number) => (v >= 0.66 ? 'var(--brace)' : v >= 0.33 ? 'var(--ambra)' : 'var(--testo-3)')
const aggiornato = computed(() => props.dati ? new Date(props.dati.aggiornato_il).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) : '')
const aperti = ref(new Set<number>()) // scomposizione espansa
const alterna = (id: number) => { const s = new Set(aperti.value); s.has(id) ? s.delete(id) : s.add(id); aperti.value = s }
</script>

<template>
  <div v-if="errore && !dati" class="p-3"><StatoErrore compatto messaggio="Non riusciamo a calcolare le aree critiche. Riprova tra poco." @riprova="emit('riprova')" /></div>
  <ul v-else-if="caricamento && !dati" class="space-y-px p-3" aria-busy="true" aria-label="Caricamento delle aree critiche">
    <li v-for="k in 4" :key="k" class="flex items-center gap-3 px-2 py-2.5">
      <span class="scheletro h-6 w-16 shrink-0" />
      <span class="flex-1 space-y-1.5"><span class="scheletro block h-3 w-36" /><span class="scheletro block h-2.5 w-24" /></span>
    </li>
  </ul>
  <div v-else-if="dati && !dati.aree.length" class="px-5 py-3.5 text-[.8rem] text-testo-2">Nessuna zona sopra la soglia di rischio alto oggi.</div>
  <div v-else-if="dati" class="min-h-0 overflow-y-auto">
    <p class="cifre px-5 pt-3 text-[.72rem] text-testo-3">Dal rischio per cella · meteo delle {{ aggiornato }}<template v-if="dati.meteo_simulato"> · meteo simulato</template></p>
    <ul class="space-y-px p-3 pt-2">
      <li v-for="a in dati.aree" :key="a.id">
        <button class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors" :class="a.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60'" :aria-current="a.id === selezionata ? 'true' : undefined" :aria-expanded="a.id === selezionata" @click="emit('seleziona', a)">
          <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: LIVELLI_AREA[a.livello].colore }" aria-hidden="true" />
          <span class="min-w-0 flex-1 pl-1 leading-tight">
            <span class="block truncate text-[.88rem] font-semibold">{{ a.nome.replace(/^\w/, (c) => c.toUpperCase()) }}</span>
            <span class="cifre mt-0.5 flex items-center gap-1 text-[.72rem] text-testo-2"><Clock class="size-3 shrink-0 text-testo-3" aria-hidden="true" />Picco {{ a.picco.dalle }}–{{ a.picco.alle }}<template v-if="a.comuni.length > 2"> · +{{ a.comuni.length - 2 }} {{ a.comuni.length === 3 ? 'comune' : 'comuni' }}</template></span>
          </span>
          <span class="shrink-0 rounded-full px-2 py-px text-[.7rem] font-semibold" :style="{ color: LIVELLI_AREA[a.livello].colore, background: `color-mix(in srgb, ${LIVELLI_AREA[a.livello].colore} 14%, transparent)` }">{{ LIVELLI_AREA[a.livello].etichetta }}</span>
        </button>
        <!-- dettaglio della zona selezionata -->
        <div v-if="a.id === selezionata" class="space-y-3 px-3 pt-2 pb-3">
          <p class="text-[.8rem] leading-snug text-testo">{{ a.motivo }}</p>
          <dl class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-[.76rem]">
            <dt class="text-testo-3">Comuni</dt><dd class="text-testo-2">{{ a.comuni.slice(0, 6).join(', ') }}<template v-if="a.comuni.length > 6"> e altri {{ a.comuni.length - 6 }}</template></dd>
            <template v-if="a.invaso">
              <dt class="text-testo-3">Acqua</dt>
              <dd class="flex items-start gap-1.5 text-testo-2"><Droplet class="mt-px size-3.5 shrink-0 text-cielo" aria-hidden="true" /><span><span class="text-testo">{{ a.invaso.nome }}</span> <span class="cifre">· {{ a.invaso.distanza_km.toLocaleString('it-IT') }} km<template v-if="a.invaso.riempimento != null"> · pieno al {{ a.invaso.riempimento }}%</template></span></span></dd>
            </template>
          </dl>
          <div>
            <button type="button" class="flex w-full items-center justify-between py-1 text-left" :aria-expanded="aperti.has(a.id)" @click="alterna(a.id)">
              <span class="etichetta">Perché è critica</span>
              <ChevronDown class="size-4 text-testo-3 transition-transform" :class="aperti.has(a.id) && 'rotate-180'" aria-hidden="true" />
            </button>
            <ul v-if="aperti.has(a.id)" class="mt-1 divide-y divide-bordo border-y border-bordo">
              <li v-for="f in a.fattori" :key="f.chiave" class="grid grid-cols-[1rem_1fr] gap-x-3 py-2">
                <component :is="ICONE[f.chiave] ?? TriangleAlert" class="mt-px size-4 text-testo-3" aria-hidden="true" />
                <div class="min-w-0">
                  <p class="flex items-baseline justify-between gap-2 text-[.8rem] font-medium leading-tight">{{ f.etichetta }}<span class="cifre text-[.74rem] text-testo-3">{{ Math.round(f.valore * 100) }}%</span></p>
                  <p class="mt-0.5 text-[.74rem] leading-snug text-testo-2">{{ f.testo }}</p>
                  <div class="relative mt-1.5 h-1 rounded-full bg-bordo-luce/70" aria-hidden="true"><span class="absolute inset-y-0 left-0 rounded-full" :style="{ width: `${Math.max(2, f.valore * 100)}%`, background: coloreFattore(f.valore) }" /></div>
                </div>
              </li>
            </ul>
          </div>
          <button type="button" class="secondario flex h-10 w-full items-center justify-center gap-1.5 text-sm" @click="emit('simula', a)"><Play class="size-4" aria-hidden="true" />Simula scenario dal punto peggiore</button>
        </div>
      </li>
    </ul>
  </div>
</template>
