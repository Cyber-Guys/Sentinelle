<script setup lang="ts">
import { Flame } from '@lucide/vue'

// Popup di un incendio storico (layer PMTiles `incendi`): proprieta' anno, data, comune, ettari, bosco_ha.
const props = defineProps<{ anno: number; data?: string; comune?: string; ettari?: number | null; bosco?: number | null }>()
defineEmits<{ chiudi: [] }>()

// stessa rampa del layer `storico` (coloriMappa): 2015 ambra tenue -> 2020 arancio -> 2025 brace
const RAMPA = { scuro: ['#c99a4a', '#ff8a3d', '#ff4a1f'], chiaro: ['#e2b45a', '#ef7a2e', '#d92d17'] }
function tintaAnno(c: string[]) {
  const t = Math.min(1, Math.max(0, (props.anno - 2015) / 10)) * 2
  const [a, b] = t <= 1 ? [c[0]!, c[1]!] : [c[1]!, c[2]!]
  return `color-mix(in srgb, ${a}, ${b} ${Math.round((t <= 1 ? t : t - 1) * 100)}%)`
}
const tinta = [tintaAnno(RAMPA.scuro), tintaAnno(RAMPA.chiaro)] as const

const num = (n: number, d = 1) => n.toLocaleString('it-IT', { maximumFractionDigits: d })
const titolo = (() => {
  const t = props.data ? new Date(props.data) : null
  return t && !isNaN(+t) ? t.toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Data non registrata'
})()
const ettari = props.ettari != null && isFinite(props.ettari) ? props.ettari : null
const bosco = ettari && props.bosco != null && isFinite(props.bosco) && props.bosco >= 0 ? Math.min(props.bosco, ettari) : null
const quota = bosco != null && ettari ? Math.round((bosco / ettari) * 100) : 0
</script>

<template>
  <PopupMappa :icona="Flame" :tinta="tinta" :etichetta="`Incendio · ${anno}`" :titolo="titolo" :sottotitolo="comune ? nomeComune(comune) : undefined" @chiudi="$emit('chiudi')">
    <dl class="popup-metriche mt-3 rounded-m p-2.5">
      <div class="flex items-baseline justify-between gap-3">
        <dt class="text-[.75rem] text-testo-2">Superficie</dt>
        <dd v-if="ettari != null" class="cifre text-right">
          <span class="text-[1.05rem] font-semibold">{{ num(ettari) }}</span> <span class="text-[.75rem] text-testo-2">ha</span>
          <span v-if="ettari >= 100" class="block text-[.7rem] text-testo-3">{{ num(ettari / 100) }} km²</span>
        </dd>
        <dd v-else class="text-[.8rem] text-testo-3">non nota</dd>
      </div>
      <div v-if="bosco != null" class="mt-2.5 border-t border-bordo pt-2.5">
        <div class="flex items-baseline justify-between gap-3">
          <dt class="text-[.75rem] text-testo-2">di cui bosco</dt>
          <dd v-if="bosco === 0" class="text-[.8rem] text-testo-3">nessuno</dd>
          <dd v-else class="cifre text-[.8rem]"><span class="font-semibold">{{ num(bosco) }}</span> <span class="text-testo-2">ha</span> <span class="text-testo-3">· {{ quota }}%</span></dd>
        </div>
        <div v-if="bosco > 0" class="mt-1.5 h-1 overflow-hidden rounded-full bg-vetro-forte" role="img" :aria-label="`Bosco ${quota}% della superficie`">
          <div class="h-full rounded-full bg-macchia" :style="{ width: `${Math.max(quota, 2)}%` }" />
        </div>
      </div>
    </dl>
  </PopupMappa>
</template>
