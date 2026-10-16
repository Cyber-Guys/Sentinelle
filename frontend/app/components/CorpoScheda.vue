<script setup lang="ts">
import { ExternalLink, Flame, ChevronRight, Check, X, Radio } from '@lucide/vue'

// Corpo della scheda di una segnalazione nel cruscotto (desktop e foglio su telefono): foto, posizione, priorita' scomposta.
defineProps<{ s: Segnalazione }>()
const emit = defineEmits<{ simula: []; stato: [v: StatoUfficiale] }>()
const nome = useId()
const { urlFoto } = useApi()
</script>

<template>
  <!-- affidabilita' della comunita', conteggi e stato ufficiale (quello che vedono i cittadini) -->
  <div class="space-y-2.5">
    <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[.78rem]">
      <span v-if="s.affidabilita" class="flex items-center gap-1.5 font-semibold" :style="{ color: LIVELLI_AFF[s.affidabilita.livello].colore }"><span class="size-2 rounded-full bg-current" aria-hidden="true" />{{ LIVELLI_AFF[s.affidabilita.livello].etichetta }}</span>
      <span class="cifre flex items-center gap-2.5 text-testo-2">
        <span class="flex items-center gap-1"><Check class="size-3.5 text-macchia" aria-hidden="true" />{{ s.conferme ?? 0 }} {{ s.conferme === 1 ? 'conferma' : 'conferme' }}</span>
        <span class="flex items-center gap-1"><X class="size-3.5" :class="s.smentite ? 'text-brace' : 'text-testo-3'" aria-hidden="true" />{{ s.smentite ?? 0 }} {{ s.smentite === 1 ? 'smentita' : 'smentite' }}</span>
      </span>
    </div>
    <p v-if="s.probabilmente_spento" class="flex items-start gap-2 rounded-m bg-ambra/12 px-3 py-2 text-[.78rem] leading-snug text-ambra"><Radio class="mt-px size-3.5 shrink-0" aria-hidden="true" /><span><span class="font-semibold">Probabilmente spento.</span> <span class="text-testo-2">I cittadini sul posto dicono che non c'è più: verifica e chiudi.</span></span></p>
    <div v-if="s.stato !== 'archiviata'">
      <p class="etichetta mb-1.5">Stato ufficiale, visibile ai cittadini</p>
      <div class="grid grid-cols-2 gap-1 rounded-m bg-vetro p-0.5 ring-1 ring-bordo sm:grid-cols-4" role="radiogroup" aria-label="Stato ufficiale">
        <label v-for="(v, k) in STATI_UFF" :key="k" class="flex min-h-9 cursor-pointer items-center justify-center rounded-s px-1.5 text-center text-[.72rem] leading-tight font-medium transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="(s.stato_ufficiale ?? 'in_verifica') === k ? 'bg-vetro-forte ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo'" :style="(s.stato_ufficiale ?? 'in_verifica') === k ? { color: v.colore } : undefined">
          <input type="radio" :name="nome" :value="k" :checked="(s.stato_ufficiale ?? 'in_verifica') === k" class="sr-only" @change="emit('stato', k)" />{{ v.etichetta }}
        </label>
      </div>
    </div>
  </div>
  <div class="grid gap-2" :class="s.foto_url ? 'grid-cols-[7.5rem_1fr]' : 'grid-cols-1'">
    <a v-if="s.foto_url" :href="urlFoto(s.foto_url)!" target="_blank" rel="noopener" class="group relative block h-[5.5rem] overflow-hidden rounded-m border border-bordo bg-vetro-forte" aria-label="Apri la foto a dimensione piena">
      <img :key="s.id" :src="urlFoto(s.foto_url)!" alt="Foto allegata alla segnalazione" class="size-full object-cover" />
      <ExternalLink class="absolute right-1.5 bottom-1.5 size-3.5 text-white opacity-0 drop-shadow transition-opacity group-hover:opacity-100" aria-hidden="true" />
    </a>
    <dl class="grid content-start gap-y-1.5 text-[.76rem]">
      <div class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Posizione</dt><dd class="cifre text-testo-2">{{ s.lat.toFixed(5) }}, {{ s.lon.toFixed(5) }}</dd></div>
      <div v-if="s.comune" class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Comune</dt><dd class="text-testo-2">{{ nomeComune(s.comune) }}</dd></div>
      <div v-if="!s.foto_url" class="flex gap-2"><dt class="w-16 shrink-0 text-testo-3">Foto</dt><dd class="text-testo-3">nessuna</dd></div>
    </dl>
  </div>
  <button type="button" class="vetro flex min-h-11 w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-vetro-forte" @click="$emit('simula')">
    <span class="flex size-8 shrink-0 items-center justify-center rounded-s bg-brace/12"><Flame class="size-4 text-brace" aria-hidden="true" /></span>
    <span class="min-w-0 flex-1 leading-tight">
      <span class="block text-[.86rem] font-semibold">Simula scenario</span>
      <span class="block text-[.72rem] text-testo-2">Dove arriverebbe il fuoco nelle prossime ore</span>
    </span>
    <ChevronRight class="size-4 shrink-0 text-testo-3" aria-hidden="true" />
  </button>
  <ScomposizionePriorita :priorita="s.priorita" :fattori="s.fattori" :motivazioni="s.motivazioni" />
</template>
