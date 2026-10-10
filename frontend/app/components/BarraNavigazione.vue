<script setup lang="ts">
import { Map as MapIcon, Target, ClipboardList, Trophy } from '@lucide/vue'

export type Scheda = 'mappa' | 'missioni' | 'segnalazioni' | 'classifica'
defineProps<{ modelValue: Scheda; avviso?: boolean }>()
defineEmits<{ 'update:modelValue': [Scheda] }>()

// quattro voci a 375 px: l'etichetta si vede solo sulla voce attiva, le altre sono icone da 44 px
const VOCI = [
  { id: 'mappa', etichetta: 'Mappa', icona: MapIcon },
  { id: 'missioni', etichetta: 'Missioni', icona: Target },
  { id: 'segnalazioni', etichetta: 'Segnalazioni', icona: ClipboardList },
  { id: 'classifica', etichetta: 'Classifica', icona: Trophy },
] as const
</script>

<template>
  <nav class="pillola fixed bottom-[max(1rem,env(safe-area-inset-bottom))] left-1/2 z-30 flex -translate-x-1/2 gap-0.5 p-1" aria-label="Sezioni">
    <button
      v-for="v in VOCI" :key="v.id" type="button"
      class="relative flex h-11 min-w-11 items-center justify-center gap-1.5 rounded-full text-[.8rem] font-medium whitespace-nowrap transition-colors duration-200"
      :class="modelValue === v.id ? 'bg-vetro-forte px-4 text-testo ring-1 ring-bordo-luce' : 'px-3 text-testo-2 hover:text-testo'"
      :aria-current="modelValue === v.id ? 'page' : undefined"
      :aria-label="v.etichetta"
      :title="v.etichetta"
      @click="$emit('update:modelValue', v.id)"
    >
      <component :is="v.icona" class="size-[18px]" :class="modelValue === v.id && 'text-brace'" aria-hidden="true" />
      <span v-if="modelValue === v.id" aria-hidden="true">{{ v.etichetta }}</span>
      <!-- segnalazioni con stato cambiato non ancora viste -->
      <span v-if="v.id === 'segnalazioni' && avviso && modelValue !== v.id" class="absolute top-2 right-2 size-2 rounded-full bg-brace ring-2 ring-fondo" aria-hidden="true" />
    </button>
  </nav>
</template>
