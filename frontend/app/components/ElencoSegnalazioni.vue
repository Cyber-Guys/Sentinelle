<script setup lang="ts">
import { Flame, TriangleAlert, ShieldCheck } from '@lucide/vue'

// Elenco del box Segnalazioni del cruscotto (colonna su desktop, foglio su telefono):
// scheda In coda con caricamento/errore/vuoto, schede valutate in sola lettura.
defineProps<{
  scheda: 'nuova' | 'confermata' | 'archiviata'
  coda: Segnalazione[]; valutate: Segnalazione[]
  caricamento: boolean; errore: string
  selezionata: number | null; appena: Set<number>
}>()
const emit = defineEmits<{ seleziona: [s: Segnalazione]; riprova: [] }>()

const VUOTO = { nuova: '', confermata: 'Nessuna segnalazione confermata', archiviata: 'Nessun falso allarme archiviato' }
const fa = (iso: string) => {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'adesso'
  if (min < 60) return `${min} min fa`
  if (min < 1440) return `${Math.round(min / 60)} h fa`
  return new Date(iso).toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
}
const faValutata = (iso: string | null | undefined) => {
  if (!iso) return ''
  const d = new Date(iso), min = Math.round((Date.now() - d.getTime()) / 60000)
  if (min < 60) return fa(iso)
  const ore = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  const giorni = Math.round((new Date().setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86400000)
  if (giorni === 0) return fa(iso)
  if (giorni === 1) return `ieri ${ore}`
  return `${d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })} ${ore}`
}
const scegli = (s: Segnalazione) => emit('seleziona', s)
</script>

<template>
  <div v-if="scheda !== 'nuova'" class="contents">
    <div v-if="!valutate.length" class="px-5 py-3.5 text-[.8rem] text-testo-2">{{ VUOTO[scheda] }}</div>
    <ul v-else class="relative min-h-0 space-y-px overflow-y-auto p-3">
      <li v-for="s in valutate" :key="s.id">
        <button class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors" :class="s.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60'" :aria-current="s.id === selezionata ? 'true' : undefined" @click="scegli(s)">
          <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: varPriorita(s.priorita) }" aria-hidden="true" />
          <span class="cifre w-8 shrink-0 text-right text-[1.05rem] font-semibold" :style="{ color: varPriorita(s.priorita) }" :aria-label="`Priorità ${s.priorita}`">{{ s.priorita }}</span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="flex items-center gap-1.5 text-[.86rem] font-medium">
              <Flame v-if="s.tipo === 'fuoco'" class="size-3.5 shrink-0 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-3.5 shrink-0 text-ambra" aria-hidden="true" />
              <span class="truncate">{{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
            </span>
            <span class="cifre mt-0.5 block text-[.72rem] text-testo-3">#{{ s.id }} · {{ faValutata(s.valutata_il) }}</span>
          </span>
          <span class="shrink-0 rounded-full px-2 py-px text-[.7rem] font-medium" :style="{ color: STATI[s.stato].colore, background: `color-mix(in srgb, ${STATI[s.stato].colore} 14%, transparent)` }">{{ STATI[s.stato].etichetta }}</span>
        </button>
      </li>
    </ul>
  </div>
  <div v-else-if="caricamento && errore" class="p-3"><StatoErrore compatto messaggio="Non riusciamo a raggiungere il servizio. La coda si aggiorna da sola appena torna la connessione." @riprova="emit('riprova')" /></div>
  <ul v-else-if="caricamento" class="space-y-px p-3" aria-busy="true" aria-label="Caricamento della coda">
    <li v-for="k in 4" :key="k" class="flex items-center gap-3 px-2 py-2.5">
      <span class="scheletro h-6 w-8 shrink-0" />
      <span class="flex-1 space-y-1.5"><span class="scheletro block h-3 w-28" /><span class="scheletro block h-2.5 w-40" /></span>
    </li>
  </ul>
  <div v-else-if="!coda.length" class="flex items-center gap-3 px-5 py-3.5">
    <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-macchia/12 text-macchia"><ShieldCheck class="size-4" aria-hidden="true" /></span>
    <div class="leading-tight">
      <p class="text-[.86rem] font-semibold">Tutto tranquillo</p>
      <p class="mt-0.5 text-[.76rem] text-testo-2">Le nuove segnalazioni compaiono qui, ordinate per priorità.</p>
    </div>
  </div>
  <TransitionGroup v-else tag="ul" name="coda" class="relative min-h-0 space-y-px overflow-y-auto p-3">
    <li v-for="s in coda" :key="s.id">
      <button
        class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors"
        :class="[s.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60', appena.has(s.id) && 'appena-arrivata']"
        :aria-current="s.id === selezionata ? 'true' : undefined"
        @click="scegli(s)"
      >
        <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: varPriorita(s.priorita) }" aria-hidden="true" />
        <span class="cifre w-8 shrink-0 text-right text-[1.05rem] font-semibold" :style="{ color: varPriorita(s.priorita) }" :aria-label="`Priorità ${s.priorita}`">{{ s.priorita }}</span>
        <span class="min-w-0 flex-1 leading-tight">
          <span class="flex items-center gap-1.5 text-[.86rem] font-medium">
            <Flame v-if="s.tipo === 'fuoco'" class="size-3.5 shrink-0 text-brace" aria-hidden="true" /><TriangleAlert v-else class="size-3.5 shrink-0 text-ambra" aria-hidden="true" />
            <span class="truncate">{{ s.tipo === 'fuoco' ? 'Fuoco / fumo' : 'Area a rischio' }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
          </span>
          <span class="cifre mt-0.5 block text-[.72rem] text-testo-3">#{{ s.id }} · {{ fa(s.creata_il) }}</span>
        </span>
        <span class="shrink-0 text-[.7rem] font-medium" :style="{ color: varPriorita(s.priorita) }">{{ etichettaPriorita(s.priorita) }}</span>
      </button>
    </li>
  </TransitionGroup>
</template>
