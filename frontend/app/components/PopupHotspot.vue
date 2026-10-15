<script setup lang="ts">
import { Satellite } from '@lucide/vue'
import { nomeComune } from '~/composables/useApi'

// Popup di un hotspot satellitare NASA FIRMS (layer `hotspot`): proprieta' di /hotspot, campi mancanti omessi.
const props = defineProps<{
  lat: number; lon: number; rilevato_il?: string; confidenza?: string; comune?: string | null
  frp?: number | null; luminosita?: number | null; satellite?: string | null; giorno?: boolean | null
}>()
defineEmits<{ chiudi: [] }>()

const tinta = ['#ff6a2b', '#c43f14'] as const // brace, come il layer
const num = (n: number, d = 1) => n.toLocaleString('it-IT', { maximumFractionDigits: d })
const NIVELLI: Record<string, [string, string]> = {
  low: ['Bassa', 'text-testo-3'], l: ['Bassa', 'text-testo-3'],
  nominal: ['Media', 'text-ambra'], n: ['Media', 'text-ambra'],
  high: ['Alta', 'text-brace'], h: ['Alta', 'text-brace'],
}
const affid = props.confidenza ? NIVELLI[props.confidenza.toLowerCase()] : undefined

const quando = props.rilevato_il ? new Date(props.rilevato_il) : null
const sottotitolo = (() => {
  if (!quando || isNaN(+quando)) return undefined
  const d = quando.toLocaleString('it-IT', { timeZone: 'Europe/Rome', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).replace(/\.?,?\s+(?=\d{2}:)/, ', ').replace('.', '')
  const min = Math.max(0, Math.round((Date.now() - +quando) / 60000))
  const rel = min < 60 ? `${min} min fa` : min < 1440 ? `${Math.floor(min / 60)} h fa` : `${Math.floor(min / 1440)} g fa`
  return `${d} · ${rel}`
})()
const sat = props.satellite ? `VIIRS · ${props.satellite}` : null
const celsius = props.luminosita != null ? Math.round(props.luminosita - 273.15) : null
</script>

<template>
  <PopupMappa :icona="Satellite" :tinta="tinta" etichetta="Hotspot satellitare" :titolo="comune ? nomeComune(comune) : 'In mare / fuori dai comuni'" :sottotitolo="sottotitolo" @chiudi="$emit('chiudi')">
    <dl v-if="affid || frp != null || luminosita != null || sat || giorno != null" class="popup-metriche mt-3 space-y-1.5 rounded-m p-2.5 text-[.75rem]">
      <div v-if="affid" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Affidabilità</dt>
        <dd class="font-semibold" :class="affid[1]">{{ affid[0] }}</dd>
      </div>
      <div v-if="frp != null" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Potenza del fuoco</dt>
        <dd class="cifre"><span class="font-semibold">{{ num(frp) }}</span> <span class="text-testo-2">MW</span></dd>
      </div>
      <div v-if="luminosita != null" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Temperatura rilevata</dt>
        <dd class="cifre"><span class="font-semibold">{{ num(luminosita, 0) }}</span> <span class="text-testo-2">K</span> <span class="text-testo-3">({{ celsius }} °C)</span></dd>
      </div>
      <div v-if="sat" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Satellite</dt>
        <dd class="cifre font-semibold">{{ sat }}</dd>
      </div>
      <div v-if="giorno != null" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Passaggio</dt>
        <dd class="font-semibold">{{ giorno ? 'Diurno' : 'Notturno' }}</dd>
      </div>
    </dl>
    <p class="cifre mt-2.5 text-[.7rem] leading-snug text-testo-3">Fonte: NASA FIRMS · risoluzione ~375 m<br />{{ lat.toFixed(4) }}, {{ lon.toFixed(4) }}</p>
  </PopupMappa>
</template>
