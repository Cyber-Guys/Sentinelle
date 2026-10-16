<script setup lang="ts">
import { TriangleAlert, Star, ChevronRight, ClipboardList, Users, ShieldCheck } from '@lucide/vue'

// Le proprie segnalazioni con lo stato della valutazione. I dati arrivano dalla pagina (polling ogni 10 s).
defineProps<{ elenco: Segnalazione[]; caricamento: boolean; errore: string; attive?: Record<number, Condivisa> }>()
defineEmits<{ apri: [Segnalazione]; riprova: [] }>()
</script>

<template>
  <div class="p-3">
    <p class="etichetta">Le tue segnalazioni</p>
    <h2 class="mt-0.5 mb-3 text-lg font-semibold tracking-tight">Conferme e stato ufficiale</h2>

    <StatoErrore v-if="errore && !elenco.length" :messaggio="errore" @riprova="$emit('riprova')" />
    <ul v-else-if="caricamento" class="space-y-1.5" aria-busy="true" aria-label="Caricamento delle segnalazioni">
      <li v-for="k in 3" :key="k" class="vetro flex items-center gap-3 px-3 py-3">
        <span class="scheletro size-8 shrink-0" />
        <span class="flex-1 space-y-1.5"><span class="scheletro block h-3 w-32" /><span class="scheletro block h-2.5 w-24" /></span>
        <span class="scheletro h-5 w-20 !rounded-full" />
      </li>
    </ul>
    <div v-else-if="!elenco.length" class="vetro flex flex-col items-center gap-3 px-5 py-8 text-center">
      <span class="flex size-12 items-center justify-center rounded-full bg-macchia/12 text-macchia ring-1 ring-macchia/25"><ClipboardList class="size-6" aria-hidden="true" /></span>
      <div class="space-y-1">
        <p class="font-semibold">Ancora nessuna segnalazione</p>
        <p class="text-[.84rem] text-testo-2">Quando vedi fumo o sterpaglie secche tocca Segnala: qui segui la valutazione degli operatori e i punti guadagnati.</p>
      </div>
    </div>
    <ul v-else class="space-y-1.5">
      <li v-for="s in elenco" :key="s.id">
        <button type="button" class="vetro flex w-full items-start gap-3 px-3 py-2.5 text-left transition-colors hover:bg-vetro-forte" :aria-label="`Segnalazione #${s.id}, ${STATI[s.stato].etichetta}: mostrala sulla mappa`" @click="$emit('apri', s)">
          <span class="flex size-8 shrink-0 items-center justify-center rounded-s" :style="{ color: TIPI[s.tipo]?.colore, background: `color-mix(in srgb, ${TIPI[s.tipo]?.colore} 13%, transparent)` }">
            <component :is="TIPI[s.tipo]?.icona ?? TriangleAlert" class="size-4" aria-hidden="true" />
          </span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block truncate text-[.88rem] font-semibold">{{ TIPI[s.tipo]?.etichetta ?? s.tipo }}<span v-if="s.comune" class="font-normal text-testo-2"> · {{ nomeComune(s.comune) }}</span></span>
            <span class="cifre mt-0.5 block truncate text-[.72rem] text-testo-3">#{{ s.id }} · {{ dataOra(s.creata_il) }}</span>
            <span class="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[.72rem]">
              <span class="flex items-center gap-1.5 rounded-full px-2 py-px font-semibold whitespace-nowrap" :style="{ color: STATI[s.stato].colore, background: `color-mix(in srgb, ${STATI[s.stato].colore} 14%, transparent)` }">
                <span class="size-1.5 rounded-full" :class="s.stato === 'archiviata' && 'ring-1 ring-current'" :style="{ background: s.stato === 'archiviata' ? 'transparent' : STATI[s.stato].colore }" aria-hidden="true" />{{ STATI[s.stato].etichetta }}
              </span>
              <span class="cifre whitespace-nowrap text-testo-2">Priorità <span class="font-semibold" :style="{ color: varPriorita(s.priorita) }">{{ s.priorita }}</span></span>
              <span v-if="s.stato_ufficiale && s.stato_ufficiale !== 'in_verifica'" class="flex items-center gap-1 font-semibold whitespace-nowrap" :style="{ color: STATI_UFF[s.stato_ufficiale].colore }"><ShieldCheck class="size-3" aria-hidden="true" />{{ STATI_UFF[s.stato_ufficiale].etichetta }}</span>
              <span v-if="attive?.[s.id]" class="flex items-center gap-1 whitespace-nowrap" :style="{ color: LIVELLI_AFF[attive[s.id]!.affidabilita.livello].colore }"><span class="size-1.5 rounded-full bg-current" aria-hidden="true" />{{ LIVELLI_AFF[attive[s.id]!.affidabilita.livello].etichetta }}</span>
              <span v-if="s.conferme" class="cifre flex items-center gap-1 whitespace-nowrap text-testo-2"><Users class="size-3" aria-hidden="true" />{{ s.conferme }} {{ s.conferme === 1 ? 'conferma' : 'conferme' }}</span>
              <span v-if="(s.punti_ottenuti ?? 0) > 0" class="cifre flex items-center gap-0.5 font-semibold text-ambra"><Star class="size-3 fill-current" aria-hidden="true" />+{{ s.punti_ottenuti }}</span>
            </span>
          </span>
          <ChevronRight class="size-4 shrink-0 self-center text-testo-3" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </div>
</template>
