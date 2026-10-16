<script setup lang="ts">
// Barra in cima alla mappa: una riga sola, che dice prima COSA e QUANTO E' VICINO, poi da dove e da quanto.
// Tre toni, sempre colore + parole: tranquillo (verde), attenzione (ambra), pericolo (rosso pieno).
import { ChevronRight, ShieldCheck } from '@lucide/vue'

defineProps<{ tono: 'tranquillo' | 'attenzione' | 'pericolo'; tipo?: TipoSegnalazione | 'rischio' | null; titolo: string; sotto?: string; altri?: number }>()
defineEmits<{ apri: [] }>()
</script>

<template>
  <button type="button" class="banner" :class="`banner-${tono}`" :aria-label="`${titolo}. ${sotto ?? ''} Tocca per i dettagli.`" @click="$emit('apri')">
    <span class="banner-icona" :class="{ 'banner-onda': tono === 'pericolo' }">
      <ShieldCheck v-if="tono === 'tranquillo' || !tipo" aria-hidden="true" />
      <IconaTipo v-else :tipo="tipo" aria-hidden="true" />
    </span>
    <span class="min-w-0 flex-1">
      <span class="banner-titolo">{{ titolo }}</span>
      <span v-if="sotto" class="banner-sotto">{{ sotto }}</span>
    </span>
    <span v-if="altri" class="banner-altri">+{{ altri }}</span>
    <ChevronRight class="size-5 flex-none opacity-80" aria-hidden="true" />
  </button>
</template>
