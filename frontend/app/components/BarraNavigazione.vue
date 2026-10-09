<script setup lang="ts">
import { Map as MapIcon, Target, Trophy } from '@lucide/vue'

export type Scheda = 'mappa' | 'missioni' | 'classifica'
defineProps<{ modelValue: Scheda }>()
defineEmits<{ 'update:modelValue': [Scheda] }>()

const VOCI = [
  { id: 'mappa', etichetta: 'Mappa', icona: MapIcon },
  { id: 'missioni', etichetta: 'Missioni', icona: Target },
  { id: 'classifica', etichetta: 'Classifica', icona: Trophy },
] as const
</script>

<template>
  <nav class="pillola fixed bottom-[max(1rem,env(safe-area-inset-bottom))] left-1/2 z-30 flex -translate-x-1/2 gap-1 p-1.5" aria-label="Sezioni">
    <button
      v-for="v in VOCI" :key="v.id" type="button"
      class="flex h-11 items-center gap-1.5 rounded-full px-4 text-[.82rem] font-semibold transition-colors duration-200"
      :class="modelValue === v.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo'"
      :aria-current="modelValue === v.id ? 'page' : undefined"
      @click="$emit('update:modelValue', v.id)"
    >
      <component :is="v.icona" class="size-[18px]" :class="modelValue === v.id && 'text-brace'" aria-hidden="true" />
      {{ v.etichetta }}
    </button>
  </nav>
</template>
