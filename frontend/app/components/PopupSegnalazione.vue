<script setup lang="ts">
import { TriangleAlert, Star, PanelRight } from '@lucide/vue'

// Popup di una segnalazione con stato (storico nel cruscotto, proprie nell'app). `azione`: "Apri scheda" (cruscotto).
const props = defineProps<{ s: Segnalazione; azione?: () => void }>()
defineEmits<{ chiudi: [] }>()

const TINTE: Record<StatoSegnalazione, readonly [string, string]> = {
  nuova: ['#f5b83d', '#956207'], confermata: ['#3fb37f', '#277752'], archiviata: ['#8a867e', '#6d6960'],
}
const st = STATI[props.s.stato]
const valutata = props.s.stato !== 'nuova'
</script>

<template>
  <PopupMappa
    :icona="TIPI[s.tipo]?.icona ?? TriangleAlert" :tinta="s.stato === 'confermata' && s.stato_ufficiale !== 'spento' ? [coloriTipi('scuro')[s.tipo], coloriTipi('chiaro')[s.tipo]] : TINTE[s.stato]"
    :etichetta="`Segnalazione #${s.id}`" :titolo="TIPI[s.tipo]?.etichetta ?? s.tipo"
    :sottotitolo="s.comune ? nomeComune(s.comune) : undefined" @chiudi="$emit('chiudi')"
  >
    <p class="mt-2 inline-flex items-center gap-1.5 rounded-full px-2 py-px text-[.74rem] font-semibold" :style="{ color: st.colore, background: `color-mix(in srgb, ${st.colore} 14%, transparent)` }">
      <span class="size-1.5 rounded-full" :class="s.stato === 'archiviata' && 'ring-1 ring-current'" :style="{ background: s.stato === 'archiviata' ? 'transparent' : st.colore }" aria-hidden="true" />{{ st.etichetta }}
    </p>
    <p v-if="s.stato_ufficiale && s.stato !== 'nuova'" class="mt-1.5 text-[.76rem] text-testo-2">
      Stato per i cittadini: <span class="font-semibold" :style="{ color: STATI_UFF[s.stato_ufficiale].colore }">{{ STATI_UFF[s.stato_ufficiale].etichetta }}</span>
    </p>
    <dl class="popup-metriche mt-2.5 space-y-1.5 rounded-m p-2.5 text-[.76rem]">
      <div class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Priorità</dt>
        <dd class="cifre font-semibold" :style="{ color: varPriorita(s.priorita) }">{{ s.priorita }} <span class="font-medium">{{ etichettaPriorita(s.priorita) }}</span></dd>
      </div>
      <div class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">{{ valutata ? 'Valutata' : 'Inviata' }}</dt>
        <dd class="cifre">{{ dataOra(valutata ? (s.valutata_il ?? s.creata_il) : s.creata_il) }}</dd>
      </div>
      <div v-if="s.conferme != null" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Comunità</dt>
        <dd class="cifre">{{ s.conferme }} {{ s.conferme === 1 ? 'conferma' : 'conferme' }} · {{ s.smentite ?? 0 }} {{ s.smentite === 1 ? 'smentita' : 'smentite' }}</dd>
      </div>
      <div v-if="s.affidabilita" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Affidabilità</dt>
        <dd class="font-semibold" :style="{ color: LIVELLI_AFF[s.affidabilita.livello].colore }">{{ LIVELLI_AFF[s.affidabilita.livello].etichetta }}</dd>
      </div>
      <div v-if="(s.punti_ottenuti ?? 0) > 0" class="flex items-baseline justify-between gap-3">
        <dt class="text-testo-2">Punti</dt>
        <dd class="cifre flex items-center gap-1 font-semibold text-ambra"><Star class="size-3 fill-current" aria-hidden="true" />+{{ s.punti_ottenuti }}</dd>
      </div>
    </dl>
    <button v-if="azione" type="button" class="secondario mt-2.5 flex h-9 w-full items-center justify-center gap-1.5 text-[.8rem]" @click="azione(); $emit('chiudi')">
      <PanelRight class="size-3.5" aria-hidden="true" /> Apri scheda
    </button>
  </PopupMappa>
</template>
