<script setup lang="ts">
import { ExternalLink, Flame, ChevronRight } from '@lucide/vue'

// Corpo della scheda di una segnalazione nel cruscotto (desktop e foglio su telefono): foto, posizione, priorita' scomposta.
defineProps<{ s: Segnalazione }>()
defineEmits<{ simula: [] }>()
const { urlFoto } = useApi()
</script>

<template>
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
