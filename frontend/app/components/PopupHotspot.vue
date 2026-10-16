<script setup lang="ts">
import { Satellite, Flame } from '@lucide/vue'
import { nomeComune } from '~/composables/useApi'

// Popup di un incendio attivo (hotspot FIRMS raggruppati, /incendi-attivi): campi mancanti omessi.
const props = defineProps<{
  lat: number; lon: number; rilevazioni: number; ettari?: number | null; prima?: string | null; ultima?: string | null
  confidenza?: string | null; comune?: string | null; frp_totale?: number | null; frp_max?: number | null; satelliti?: string | null
  onSimula?: () => void
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
const relativo = (iso?: string | null) => {
  const q = iso ? new Date(iso) : null
  if (!q || isNaN(+q)) return null
  const min = Math.max(0, Math.round((Date.now() - +q) / 60000))
  const ora = q.toLocaleTimeString('it-IT', { timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit' })
  return `${min < 60 ? `${min} min fa` : min < 1440 ? `${Math.floor(min / 60)} h fa` : `${Math.floor(min / 1440)} g fa`} · ${ora}`
}
const prima = relativo(props.prima)
const ultima = relativo(props.ultima)
// etichetta corta (il badge tronca): il numero di rilevazioni va nel sottotitolo
const sottotitolo = [`${props.rilevazioni} ${props.rilevazioni === 1 ? 'rilevazione' : 'rilevazioni'}`, props.ettari != null ? `area stimata ~${num(props.ettari, 0)} ha` : null].filter(Boolean).join(' · ')
</script>

<template>
  <PopupMappa :icona="Satellite" :tinta="tinta" etichetta="Incendio attivo" :titolo="comune ? nomeComune(comune) : 'In mare / fuori dai comuni'" :sottotitolo="sottotitolo" @chiudi="$emit('chiudi')">
    <dl class="popup-metriche mt-3 space-y-1.5 rounded-m p-2.5 text-[.75rem]">
      <div v-if="prima" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">{{ rilevazioni > 1 ? 'Prima rilevazione' : 'Rilevato' }}</dt>
        <dd class="cifre font-semibold">{{ prima }}</dd>
      </div>
      <div v-if="ultima && rilevazioni > 1" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Ultima rilevazione</dt>
        <dd class="cifre font-semibold">{{ ultima }}</dd>
      </div>
      <div v-if="frp_totale != null" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">{{ rilevazioni > 1 ? 'Potenza totale / max' : 'Potenza del fuoco' }}</dt>
        <dd class="cifre"><span class="font-semibold">{{ num(frp_totale) }}</span><template v-if="rilevazioni > 1 && frp_max != null"> / <span class="font-semibold">{{ num(frp_max) }}</span></template> <span class="text-testo-2">MW</span></dd>
      </div>
      <div v-if="affid" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Affidabilità</dt>
        <dd class="font-semibold" :class="affid[1]">{{ affid[0] }}</dd>
      </div>
      <div v-if="satelliti" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Satelliti</dt>
        <dd class="cifre text-right font-semibold">VIIRS · {{ satelliti }}</dd>
      </div>
    </dl>
    <p class="cifre mt-2.5 text-[.7rem] leading-snug text-testo-3">Fonte: NASA FIRMS · pixel ~375 m uniti<br />{{ lat.toFixed(4) }}, {{ lon.toFixed(4) }}</p>
    <button v-if="onSimula" type="button" class="primario mt-3 flex h-9 w-full items-center justify-center gap-1.5 text-[.8rem]" @click="onSimula"><Flame class="size-3.5" aria-hidden="true" />Simula scenario dall'area</button>
  </PopupMappa>
</template>
