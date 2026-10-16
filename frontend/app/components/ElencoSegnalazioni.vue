<script setup lang="ts">
import { ShieldCheck, Check, X } from '@lucide/vue'

// Elenco del box Segnalazioni del cruscotto (colonna su desktop, foglio su telefono):
// scheda In coda con caricamento/errore/vuoto, schede valutate in sola lettura.
const props = defineProps<{
  scheda: 'nuova' | 'confermata' | 'archiviata'
  coda: Segnalazione[]; tutte?: Segnalazione[]; valutate: Segnalazione[]
  caricamento: boolean; errore: string
  selezionata: number | null; appena: Set<number>
}>()
const filtro = defineModel<TipoSegnalazione | null>('filtro', { default: null })
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
const BREVE_LIV = { da_verificare: 'Da verificare', probabile: 'Probabile', comunita: 'Comunità', operatori: 'Operatori' } as const
const nTipo = (props_tutte: Segnalazione[], k: TipoSegnalazione) => props_tutte.filter((s) => s.tipo === k).length
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
              <component :is="TIPI[s.tipo].icona" class="size-3.5 shrink-0" :style="{ color: TIPI[s.tipo].colore }" aria-hidden="true" />
              <span class="truncate">{{ TIPI[s.tipo].etichetta }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
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
  <div v-else class="flex min-h-0 flex-col">
    <div v-if="(tutte?.length ?? 0) > 1" class="flex shrink-0 gap-1.5 overflow-x-auto px-3 pt-2.5 pb-0.5" role="group" aria-label="Filtra per tipo">
      <button type="button" class="tocco flex h-7 shrink-0 items-center gap-1.5 rounded-full px-2.5 text-[.74rem] font-medium whitespace-nowrap ring-1 transition-colors" :class="!filtro ? 'bg-vetro-forte text-testo ring-bordo-luce' : 'text-testo-2 ring-bordo hover:text-testo'" :aria-pressed="!filtro" @click="filtro = null">Tutti <span class="cifre text-testo-3">{{ tutte!.length }}</span></button>
      <button v-for="k in ORDINE_TIPI.filter((k) => nTipo(tutte!, k))" :key="k" type="button" class="tocco flex h-7 shrink-0 items-center gap-1.5 rounded-full px-2.5 text-[.74rem] font-medium whitespace-nowrap ring-1 transition-colors" :class="filtro === k ? 'bg-vetro-forte text-testo ring-bordo-luce' : 'text-testo-2 ring-bordo hover:text-testo'" :aria-pressed="filtro === k" :aria-label="TIPI[k].etichetta" :title="TIPI[k].etichetta" @click="filtro = filtro === k ? null : k">
        <component :is="TIPI[k].icona" class="size-3.5" :style="{ color: TIPI[k].colore }" aria-hidden="true" /><span class="cifre">{{ nTipo(tutte!, k) }}</span>
      </button>
    </div>
    <div v-if="!coda.length && !tutte?.length" class="flex items-center gap-3 px-5 py-3.5">
      <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-macchia/12 text-macchia"><ShieldCheck class="size-4" aria-hidden="true" /></span>
      <div class="leading-tight">
        <p class="text-[.86rem] font-semibold">Tutto tranquillo</p>
        <p class="mt-0.5 text-[.76rem] text-testo-2">Le nuove segnalazioni compaiono qui, ordinate per priorità.</p>
      </div>
    </div>
    <p v-else-if="!coda.length" class="px-5 py-3.5 text-[.8rem] text-testo-2">Nessuna segnalazione di questo tipo in coda.</p>
    <TransitionGroup v-else tag="ul" name="coda" class="relative min-h-0 space-y-px overflow-y-auto p-3">
      <li v-for="s in coda" :key="s.id">
        <button
          class="relative flex w-full items-center gap-3 rounded-m px-2 py-2 text-left transition-colors"
          :class="[s.id === selezionata ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'hover:bg-vetro-forte/60', s.probabilmente_spento && s.id !== selezionata && 'ring-1 ring-ambra/50 bg-ambra/[.06]', appena.has(s.id) && 'appena-arrivata']"
          :aria-current="s.id === selezionata ? 'true' : undefined"
          @click="scegli(s)"
        >
          <span class="absolute inset-y-3 left-0 w-[3px] rounded-full" :style="{ background: varPriorita(s.priorita) }" aria-hidden="true" />
          <span class="cifre w-8 shrink-0 text-right text-[1.05rem] font-semibold" :style="{ color: varPriorita(s.priorita) }" :aria-label="`Priorità ${s.priorita}`">{{ s.priorita }}</span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="flex items-center gap-1.5 text-[.86rem] font-medium">
              <component :is="TIPI[s.tipo].icona" class="size-3.5 shrink-0" :style="{ color: TIPI[s.tipo].colore }" aria-hidden="true" />
              <span class="truncate">{{ TIPI[s.tipo].etichetta }}<template v-if="s.comune"> · {{ nomeComune(s.comune) }}</template></span>
            </span>
            <span class="cifre mt-0.5 flex items-center gap-1.5 text-[.72rem] text-testo-3">
              <span class="shrink-0">#{{ s.id }} · {{ fa(s.creata_il) }}</span>
              <span v-if="s.conferme || s.smentite" class="flex shrink-0 items-center gap-1" :aria-label="`${s.conferme ?? 0} conferme, ${s.smentite ?? 0} smentite`">
                <span class="flex items-center gap-px text-macchia"><Check class="size-3" aria-hidden="true" />{{ s.conferme ?? 0 }}</span>
                <span class="flex items-center gap-px" :class="s.smentite ? 'text-brace' : ''"><X class="size-3" aria-hidden="true" />{{ s.smentite ?? 0 }}</span>
              </span>
              <span v-if="s.affidabilita" class="flex min-w-0 items-center gap-1 font-sans font-medium" :style="{ color: LIVELLI_AFF[s.affidabilita.livello].colore }"><span class="size-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" /><span class="truncate">{{ BREVE_LIV[s.affidabilita.livello] }}</span></span>
            </span>
          </span>
          <span v-if="s.probabilmente_spento" class="shrink-0 rounded-full bg-ambra/15 px-2 py-px text-[.7rem] font-semibold text-ambra">Probabilmente spento</span>
          <span v-else class="shrink-0 text-[.7rem] font-medium" :style="{ color: varPriorita(s.priorita) }">{{ etichettaPriorita(s.priorita) }}</span>
        </button>
      </li>
    </TransitionGroup>
  </div>
</template>
