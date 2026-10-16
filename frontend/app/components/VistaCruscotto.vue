<script setup lang="ts">
// Schede principali del cruscotto: coda delle segnalazioni o aree critiche di oggi.
defineProps<{ nCoda: number; nAree: number; grande?: boolean }>()
const vista = defineModel<'segnalazioni' | 'aree'>({ required: true })
</script>

<template>
  <div class="flex gap-1" role="tablist" aria-label="Vista del cruscotto">
    <button v-for="v in ([{ id: 'segnalazioni', etichetta: 'Segnalazioni', n: nCoda }, { id: 'aree', etichetta: 'Aree critiche', n: nAree }] as const)" :key="v.id" type="button" role="tab" :aria-selected="vista === v.id"
      class="flex items-center gap-1.5 rounded-full px-2.5 font-semibold whitespace-nowrap transition-colors"
      :class="[grande ? 'h-11 text-[.92rem]' : 'h-8 text-[.9rem]', vista === v.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-3 hover:text-testo']"
      @click="vista = v.id">
      {{ v.etichetta }}<span class="cifre text-[.78rem]" :class="v.n && v.id === 'aree' ? 'text-brace' : 'text-testo-3'">{{ v.n }}</span>
    </button>
  </div>
</template>
