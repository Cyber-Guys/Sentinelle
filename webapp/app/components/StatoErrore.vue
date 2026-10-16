<script setup lang="ts">
import { CloudOff } from '@lucide/vue'

defineProps<{ testo?: string }>()
defineEmits<{ riprova: [] }>()
</script>

<template>
  <div class="scheda flex flex-col items-center gap-3 py-8 text-center" role="alert">
    <span class="grid size-14 place-items-center rounded-full bg-brace-fondo text-brace"><CloudOff class="size-7" aria-hidden="true" /></span>
    <p class="max-w-[18rem] text-lg font-bold">{{ testo ?? 'Non riesco a caricare i dati.' }}</p>
    <button type="button" class="pulsante pulsante-scuro" @click="$emit('riprova')">Riprova</button>
  </div>
</template>
