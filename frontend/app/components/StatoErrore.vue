<script setup lang="ts">
// Errore di caricamento: frase non tecnica e un'azione sola, "Riprova". Stesso vetro del contenuto che sostituisce.
import { CloudOff, RotateCw } from '@lucide/vue'

withDefaults(defineProps<{ messaggio: string; titolo?: string; compatto?: boolean }>(), { titolo: 'Connessione assente' })
defineEmits<{ riprova: [] }>()
</script>

<template>
  <div class="vetro flex flex-col items-center text-center" :class="compatto ? 'gap-2 p-4' : 'gap-3 px-5 py-7'" role="alert">
    <span class="flex items-center justify-center rounded-full bg-ambra/12 text-ambra ring-1 ring-ambra/25" :class="compatto ? 'size-10' : 'size-12'">
      <CloudOff :class="compatto ? 'size-5' : 'size-6'" aria-hidden="true" />
    </span>
    <div class="space-y-1">
      <p class="font-semibold">{{ titolo }}</p>
      <p class="text-[.84rem] text-testo-2">{{ messaggio }}</p>
    </div>
    <button type="button" class="secondario mt-1 flex h-11 items-center gap-2 px-5 text-sm" @click="$emit('riprova')">
      <RotateCw class="size-4" aria-hidden="true" /> Riprova
    </button>
  </div>
</template>
