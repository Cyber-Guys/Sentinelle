<script setup lang="ts">
import { ChevronDown, ShieldCheck } from '@lucide/vue'

// Popup di una segnalazione della mappa condivisa. `v` e' reattivo (lo aggiorna la pagina): dopo un voto
// o un evento SSE il contenuto cambia senza riaprire il popup.
export type VistaCondivisa = {
  s: Condivisa | null; foto: string | null; pos: { lat: number; lon: number } | null; gps: string; inCorso: boolean; errore: string
}
const props = defineProps<{ v: VistaCondivisa; vota: (voto: 'ancora' | 'finito') => void }>()
defineEmits<{ chiudi: [] }>()

const aperti = ref(false)
const s = computed(() => props.v.s!)
const t = computed(() => TIPI[s.value.tipo])
const tinta = computed(() => [coloriTipi('scuro')[s.value.tipo], coloriTipi('chiaro')[s.value.tipo]] as const)
const liv = computed(() => LIVELLI_AFF[s.value.affidabilita.livello])
const uff = computed(() => STATI_UFF[s.value.stato_ufficiale])
const dist = computed(() => (props.v.pos ? distanzaM(props.v.pos, s.value) : null))
// perche' i pulsanti sono spenti (null = si puo' votare)
const motivo = computed(() => {
  if (s.value.mia) return 'È una tua segnalazione: la confermano gli altri.'
  if (s.value.stato_ufficiale === 'spento') return 'Gli operatori l\'hanno chiusa come spenta.'
  if (dist.value === null) return props.v.gps
  if (dist.value > RAGGIO_VOTO_M) return `Sei a ${distanzaTesto(dist.value)}: puoi confermare solo entro 2 km.`
  return null
})
const fattori = computed(() => s.value.affidabilita.fattori.filter((f) => f.contributo !== 0))
const segno = (c: number) => (c > 0 ? '+' : '−') + Math.abs(c).toLocaleString('it-IT', { maximumFractionDigits: 1 })
</script>

<template>
  <PopupMappa :icona="t.icona" :tinta="tinta" :etichetta="`${daQuanto(s.creata_il)}${dist !== null ? ' · a ' + distanzaTesto(dist) : ''}`" :titolo="t.etichetta" @chiudi="$emit('chiudi')">
    <div class="mt-2 flex flex-wrap items-center gap-1.5">
      <span class="inline-flex items-center gap-1.5 rounded-full px-2 py-px text-[.74rem] font-semibold" :style="{ color: uff.colore, background: `color-mix(in srgb, ${uff.colore} 14%, transparent)` }">
        <ShieldCheck class="size-3" aria-hidden="true" />{{ uff.etichetta }}
      </span>
      <span v-if="s.probabilmente_spento" class="inline-flex items-center rounded-full px-2 py-px text-[.74rem] font-semibold text-testo-2 ring-1 ring-bordo-luce">Probabilmente spento</span>
      <span v-if="s.mia" class="inline-flex items-center rounded-full px-2 py-px text-[.74rem] font-medium text-testo-2 ring-1 ring-bordo-luce">Tua</span>
    </div>

    <img v-if="v.foto" :src="v.foto" alt="Foto della segnalazione" class="mt-2.5 h-28 w-full rounded-m object-cover" loading="lazy" />

    <VotoCondivisa class="mt-2.5" :s="s" :motivo="motivo" :in-corso="v.inCorso" :errore="v.errore" @vota="vota" />

    <button type="button" class="mt-2 flex w-full items-center gap-1.5 text-left text-[.74rem] text-testo-3 hover:text-testo-2" :aria-expanded="aperti" @click="aperti = !aperti">
      <span class="flex-1">Perché è {{ liv.etichetta.toLowerCase() }}</span>
      <ChevronDown class="size-3.5 transition-transform" :class="aperti && 'rotate-180'" aria-hidden="true" />
    </button>
    <ul v-if="aperti" class="popup-metriche mt-1 space-y-0.5 rounded-m p-2.5 text-[.74rem]">
      <li v-for="f in fattori" :key="f.chiave" class="flex justify-between gap-3"><span class="text-testo-2">{{ f.etichetta.replace(`c'e' piu'`, `c'è più`) }}</span><span class="cifre font-medium" :class="f.contributo < 0 && 'text-testo-3'">{{ segno(f.contributo) }}</span></li>
      <li class="flex justify-between gap-3 border-t border-bordo pt-0.5 font-semibold"><span>Totale</span><span class="cifre">{{ s.affidabilita.valore.toLocaleString('it-IT', { maximumFractionDigits: 1 }) }}</span></li>
    </ul>
  </PopupMappa>
</template>
