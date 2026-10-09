<script setup lang="ts">
// Anello di avanzamento verso il prossimo livello attorno alle iniziali.
const props = withDefaults(defineProps<{ nome?: string; progresso: number; dimensione?: number }>(), { dimensione: 44 })

const R = 15.5
const C = 2 * Math.PI * R
const tratto = computed(() => Math.max(0, Math.min(1, props.progresso)) * C)
const iniziali = computed(() =>
  (props.nome ?? "").replace(/\(.*?\)/g, '').trim().split(/\s+/).map((p) => p[0]).join('').slice(0, 2).toUpperCase(),
)
const id = useId()
</script>

<template>
  <svg :width="dimensione" :height="dimensione" viewBox="0 0 36 36" role="img" :aria-label="`${Math.round(progresso * 100)} per cento verso il prossimo livello`" class="shrink-0">
    <defs>
      <linearGradient :id="id" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#ffb347" />
        <stop offset="100%" stop-color="#ff4a1f" />
      </linearGradient>
    </defs>
    <circle cx="18" cy="18" r="13" fill="var(--vetro-forte)" />
    <circle cx="18" cy="18" :r="R" fill="none" stroke="var(--bordo-luce)" stroke-width="3" />
    <circle
      cx="18" cy="18" :r="R" fill="none" :stroke="`url(#${id})`" stroke-width="3" stroke-linecap="round"
      :stroke-dasharray="`${tratto} ${C}`" transform="rotate(-90 18 18)" class="transition-[stroke-dasharray] duration-700"
    />
    <text x="18" y="18.6" text-anchor="middle" dominant-baseline="middle" font-size="10.5" font-weight="700" fill="var(--testo)">{{ iniziali }}</text>
  </svg>
</template>
