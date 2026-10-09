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
  <nav class="grid grid-cols-3 border-t border-bordo bg-carta">
    <button v-for="v in VOCI" :key="v.id" type="button" class="flex flex-col items-center gap-0.5 py-2 text-xs font-semibold" :class="modelValue === v.id ? 'text-fuoco' : 'text-testo-2'" @click="$emit('update:modelValue', v.id)">
      <component :is="v.icona" class="size-6" />
      {{ v.etichetta }}
    </button>
  </nav>
</template>
