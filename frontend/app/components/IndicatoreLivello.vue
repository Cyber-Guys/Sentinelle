<script setup lang="ts">
import { Star } from '@lucide/vue'
import type { Livello } from '~/composables/useApi'

defineProps<{ punti: number; livello?: Livello }>()
</script>

<template>
  <div class="min-w-0 flex-1">
    <div class="flex items-center justify-between gap-2 text-xs">
      <span class="truncate font-bold text-bosco">{{ livello?.nome ?? 'Osservatore' }}</span>
      <span class="flex shrink-0 items-center gap-1 font-bold text-bosco"><Star class="size-3.5" /> {{ punti }}</span>
    </div>
    <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-bosco-chiaro">
      <div class="h-full rounded-full bg-fuoco transition-all duration-700" :style="{ width: Math.round((livello?.progresso ?? 0) * 100) + '%' }" />
    </div>
    <p class="mt-0.5 text-[10px] text-testo-2">{{ livello?.prossima_soglia ? `Prossimo livello a ${livello.prossima_soglia} punti` : 'Livello massimo' }}</p>
  </div>
</template>
