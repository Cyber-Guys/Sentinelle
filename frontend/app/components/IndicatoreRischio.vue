<script setup lang="ts">
import { Wind, Droplet, SunMedium, Thermometer } from '@lucide/vue'
import type { Rischio } from '~/composables/useApi'

const props = defineProps<{ rischio: Rischio | null }>()
const aperto = ref(false)

type Meteo = { vento_kmh?: number; raffiche_kmh?: number; umidita?: number; temperatura?: number; giorni_senza_pioggia?: number }
const meteo = computed(() => (props.rischio?.meteo ?? {}) as Meteo)
const colore = computed(() =>
  props.rischio?.livello === 'alto' ? 'var(--brace)' : props.rischio?.livello === 'medio' ? 'var(--ambra)' : 'var(--macchia)',
)
// semicerchio: lunghezza dell'arco proporzionale al valore 0-1
const ARCO = Math.PI * 14
const tratto = computed(() => Math.max(0.04, Math.min(1, props.rischio?.valore ?? 0)) * ARCO)

const righe = computed(() => [
  { icona: Wind, etichetta: 'Vento', valore: meteo.value.vento_kmh != null ? `${Math.round(meteo.value.vento_kmh)} km/h` : 'n.d.', nota: meteo.value.raffiche_kmh != null ? `raffiche ${Math.round(meteo.value.raffiche_kmh)}` : '' },
  { icona: Droplet, etichetta: 'Umidità', valore: meteo.value.umidita != null ? `${meteo.value.umidita}%` : 'n.d.', nota: '' },
  { icona: SunMedium, etichetta: 'Senza pioggia', valore: meteo.value.giorni_senza_pioggia != null ? `${meteo.value.giorni_senza_pioggia} gg` : 'n.d.', nota: '' },
  { icona: Thermometer, etichetta: 'Temperatura', valore: meteo.value.temperatura != null ? `${Math.round(meteo.value.temperatura)}°` : 'n.d.', nota: '' },
])
</script>

<template>
  <div class="relative">
    <button
      type="button"
      class="pillola flex h-12 items-center gap-2 py-1 pr-3.5 pl-2.5"
      :aria-expanded="aperto"
      aria-label="Rischio incendio di oggi: mostra i dettagli"
      @click="aperto = !aperto"
    >
      <svg width="28" height="18" viewBox="0 0 34 21" aria-hidden="true">
        <path d="M3 18a14 14 0 0 1 28 0" fill="none" stroke="var(--bordo-luce)" stroke-width="3.5" stroke-linecap="round" />
        <path v-if="rischio" d="M3 18a14 14 0 0 1 28 0" fill="none" :stroke="colore" stroke-width="3.5" stroke-linecap="round" :stroke-dasharray="`${tratto} 100`" />
      </svg>
      <span class="text-left leading-none">
        <span class="block text-[.6rem] font-semibold uppercase tracking-wide text-testo-3">Rischio</span>
        <span v-if="rischio" class="mt-0.5 block text-[.86rem] font-bold capitalize" :style="{ color: colore }">{{ rischio.livello }}</span>
        <span v-else class="mt-0.5 block text-[.86rem] text-testo-3">…</span>
      </span>
    </button>

    <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0 -translate-y-1" leave-active-class="transition duration-150" leave-to-class="opacity-0 -translate-y-1">
      <div v-if="aperto && rischio" class="sospeso absolute right-0 top-14 z-30 w-60 p-4">
        <div class="flex items-baseline justify-between">
          <span class="etichetta">Indice di oggi</span>
          <span class="cifre text-2xl font-bold" :style="{ color: colore }">{{ Math.round(rischio.valore * 100) }}<span class="text-sm text-testo-3">/100</span></span>
        </div>
        <ul class="mt-3 space-y-2 text-[.84rem]">
          <li v-for="r in righe" :key="r.etichetta" class="flex items-center gap-2">
            <component :is="r.icona" class="size-4 text-testo-3" aria-hidden="true" />
            <span class="flex-1 text-testo-2">{{ r.etichetta }}</span>
            <span class="cifre font-semibold">{{ r.valore }}</span>
            <span v-if="r.nota" class="cifre text-[.7rem] text-testo-3">{{ r.nota }}</span>
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>
