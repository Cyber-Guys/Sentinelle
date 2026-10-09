<script setup lang="ts">
// Priorita' (0-100) come numero grande dentro un anello colorato.
const props = withDefaults(defineProps<{ valore: number; dimensione?: number; spessore?: number }>(), { dimensione: 48, spessore: 3.2 })

const R = 15.5
const C = 2 * Math.PI * R
const tratto = computed(() => Math.max(0.03, Math.min(1, props.valore / 100)) * C)
const colore = computed(() => varPriorita(props.valore))
</script>

<template>
  <svg :width="dimensione" :height="dimensione" viewBox="0 0 36 36" role="img" :aria-label="`Priorità ${etichettaPriorita(valore).toLowerCase()}, ${valore} su 100`" class="shrink-0">
    <circle cx="18" cy="18" :r="R" fill="none" stroke="var(--bordo-luce)" :stroke-width="spessore" />
    <circle
      cx="18" cy="18" :r="R" fill="none" :stroke="colore" :stroke-width="spessore" stroke-linecap="round"
      :stroke-dasharray="`${tratto} ${C}`" transform="rotate(-90 18 18)"
      :style="{ filter: valore >= 60 ? 'drop-shadow(0 0 2px rgba(255,90,31,.6))' : undefined }"
    />
    <text x="18" y="18.8" text-anchor="middle" dominant-baseline="middle" font-size="12" font-weight="750" fill="var(--testo)" class="cifre">{{ valore }}</text>
  </svg>
</template>
