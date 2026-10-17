<script setup lang="ts">
import { Layers, ChevronDown, ShieldAlert, Flame, History, Droplets, Building2, Binoculars, Truck, Plane, FlameKindling, Siren, CircleDashed } from '@lucide/vue'
import type { Component } from 'vue'
import type { Livelli } from './MappaCop.vue'

const livelli = defineModel<Livelli>('livelli', { required: true })
const giorno = defineModel<'oggi' | 'domani'>('giorno', { required: true })
const anni = defineModel<[number, number]>('anni', { required: true })
defineProps<{ conteggi: Partial<Record<keyof Livelli, number | string>> }>()

const aperto = ref(true)
type Voce = { id: keyof Livelli; titolo: string; icona: Component; tinta: string }
const GRUPPI: { titolo: string; voci: Voce[] }[] = [
  { titolo: 'Rischio', voci: [{ id: 'rischio', titolo: 'Bollettino CFD', icona: ShieldAlert, tinta: 'var(--allerta-arancione)' }] },
  { titolo: 'Incendi', voci: [
    { id: 'incendi', titolo: 'Incendi attivi', icona: Flame, tinta: 'var(--brace)' },
    { id: 'spenti', titolo: 'Aree spente (72 h)', icona: CircleDashed, tinta: 'var(--testo-3)' },
    { id: 'storico', titolo: 'Storico CFVA', icona: History, tinta: 'var(--ambra)' },
    { id: 'segnalazioni', titolo: 'Segnalazioni da verificare', icona: Siren, tinta: 'var(--ambra)' },
  ] },
  { titolo: 'Risorse', voci: [
    { id: 'invasi', titolo: "Riserve d'acqua", icona: Droplets, tinta: 'var(--cielo)' },
    { id: 'basi', titolo: 'Stazioni e basi', icona: Building2, tinta: 'var(--testo-2)' },
    { id: 'vedette', titolo: 'Vedette e raggio', icona: Binoculars, tinta: 'var(--cielo)' },
    { id: 'terra', titolo: 'Mezzi terrestri', icona: Truck, tinta: 'var(--testo-2)' },
    { id: 'aerei', titolo: 'Mezzi aerei', icona: Plane, tinta: 'var(--testo-2)' },
    { id: 'fuochi', titolo: 'Fuochi autorizzati', icona: FlameKindling, tinta: 'var(--viola)' },
  ] },
]
const alterna = (id: keyof Livelli) => (livelli.value = { ...livelli.value, [id]: !livelli.value[id] })
const accesi = computed(() => Object.values(livelli.value).filter(Boolean).length)

// cursore doppio: i due estremi non si incrociano
function anno(i: 0 | 1, v: string) {
  const n = Number(v), a: [number, number] = [...anni.value]
  a[i] = i === 0 ? Math.min(n, a[1]) : Math.max(n, a[0])
  anni.value = a
}
</script>

<template>
  <section class="livelli pillola-pannello flex w-[272px] flex-col overflow-hidden" :class="{ chiuso: !aperto }" aria-label="Livelli della mappa">
    <button type="button" class="flex h-11 shrink-0 items-center gap-2.5 px-3.5 text-left" :aria-expanded="aperto" @click="aperto = !aperto">
      <Layers class="size-4 text-testo-2" aria-hidden="true" />
      <span class="flex-1 text-[.86rem] font-semibold">Livelli</span>
      <span class="cifre text-[.74rem] text-testo-3">{{ accesi }} attivi</span>
      <ChevronDown class="freccia size-4 text-testo-3" aria-hidden="true" />
    </button>
    <div class="corpo-wrap">
      <div class="corpo cop-scroll min-h-0 overflow-y-auto px-2 pb-2">
        <div v-for="g in GRUPPI" :key="g.titolo" class="mt-1 first:mt-0">
          <h3 class="px-1.5 pt-2 pb-1 text-[.72rem] font-medium text-testo-3">{{ g.titolo }}</h3>
          <template v-for="v in g.voci" :key="v.id">
            <button type="button" class="riga flex w-full items-center gap-2.5 rounded-m px-1.5 py-1.5 text-left" :aria-pressed="livelli[v.id]" @click="alterna(v.id)">
              <span class="icona flex size-7 shrink-0 items-center justify-center rounded-s" :style="{ '--t': v.tinta }" aria-hidden="true">
                <component :is="v.icona" class="size-3.5" />
              </span>
              <span class="min-w-0 flex-1 truncate text-[.82rem]" :class="livelli[v.id] ? 'text-testo' : 'text-testo-2'">{{ v.titolo }}</span>
              <span v-if="conteggi[v.id] != null" class="cifre text-[.74rem] text-testo-3">{{ conteggi[v.id] }}</span>
              <span class="interruttore" :class="{ acceso: livelli[v.id] }" aria-hidden="true" />
            </button>
            <!-- opzioni della voce, solo se accesa -->
            <div v-if="v.id === 'rischio' && livelli.rischio" class="mb-1 ml-[46px] mr-1.5 flex rounded-full bg-vetro p-0.5" role="radiogroup" aria-label="Giorno del bollettino">
              <button v-for="gg in (['oggi', 'domani'] as const)" :key="gg" type="button" role="radio" :aria-checked="giorno === gg"
                class="segmento h-7 flex-1 rounded-full text-[.76rem] font-medium" :class="giorno === gg ? 'attivo' : 'text-testo-3'" @click="giorno = gg">
                {{ gg === 'oggi' ? 'Oggi' : 'Domani' }}
              </button>
            </div>
            <div v-if="v.id === 'storico' && livelli.storico" class="mb-1.5 ml-[46px] mr-1.5">
              <div class="flex justify-between text-[.74rem]"><span class="cifre font-medium">{{ anni[0] }}</span><span class="cifre font-medium">{{ anni[1] }}</span></div>
              <div class="doppio relative mt-1 h-5">
                <div class="binario absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-vetro-forte" />
                <div class="absolute top-1/2 h-1 -translate-y-1/2 rounded-full bg-ambra" :style="{ left: `${((anni[0] - 2005) / 20) * 100}%`, right: `${100 - ((anni[1] - 2005) / 20) * 100}%` }" />
                <input type="range" min="2005" max="2025" :value="anni[0]" aria-label="Dall'anno" @input="anno(0, ($event.target as HTMLInputElement).value)">
                <input type="range" min="2005" max="2025" :value="anni[1]" aria-label="All'anno" @input="anno(1, ($event.target as HTMLInputElement).value)">
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pillola-pannello {
  background: var(--vetro-mappa);
  border: 1px solid var(--bordo);
  border-top-color: var(--bordo-luce);
  border-radius: var(--radius-l);
  backdrop-filter: blur(20px) saturate(160%);
  box-shadow: var(--ombra);
  max-height: calc(100% - 32px);
}
/* apertura: altezza con grid-template-rows (niente misure in JS), contenuto che sfuma */
.corpo-wrap { display: grid; grid-template-rows: 1fr; min-height: 0; transition: grid-template-rows 260ms var(--ease-out); }
.chiuso .corpo-wrap { grid-template-rows: 0fr; }
.corpo { transition: opacity 200ms ease; }
.chiuso .corpo { opacity: 0; }
.freccia { transition: rotate 220ms var(--ease-out); }
.chiuso .freccia { rotate: -90deg; }
.riga { transition: background-color 150ms ease; }
@media (hover: hover) { .riga:hover { background: var(--vetro-forte); } }
.icona { color: var(--t); background: color-mix(in srgb, var(--t) 14%, transparent); transition: opacity 150ms ease; }
.riga[aria-pressed='false'] .icona { opacity: 0.55; }
.segmento { transition: background-color 160ms ease, color 160ms ease; }
.segmento.attivo { background: var(--vetro-forte); color: var(--testo); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2), inset 0 0 0 1px var(--bordo-luce); }
.doppio input { position: absolute; inset: 0; width: 100%; appearance: none; background: none; pointer-events: none; margin: 0; }
.doppio input::-webkit-slider-thumb { appearance: none; pointer-events: auto; width: 16px; height: 16px; border-radius: 999px; background: var(--testo); border: 3px solid var(--ambra); box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4); cursor: grab; }
.doppio input::-moz-range-thumb { pointer-events: auto; width: 12px; height: 12px; border-radius: 999px; background: var(--testo); border: 3px solid var(--ambra); cursor: grab; }
.doppio input:focus-visible::-webkit-slider-thumb { outline: 2px solid var(--cielo); outline-offset: 2px; }
</style>
