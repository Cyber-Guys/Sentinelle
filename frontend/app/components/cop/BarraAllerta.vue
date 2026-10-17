<script setup lang="ts">
import { LIVELLI_CFD, fmtPct, type Quote, type LivelloCfd } from '~/composables/useCop'

// Quota dell'area per livello del bollettino: barra impilata con spazi di 2 px, sempre con parola e percentuale
const props = defineProps<{ quote: Quote }>()
const ORDINE: LivelloCfd[] = ['rosso', 'arancione', 'verde']
const parti = computed(() => ORDINE.map((l) => ({ l, q: props.quote[l] })).filter((p) => p.q > 0.004))
</script>

<template>
  <div>
    <div class="flex h-2.5 gap-[2px] overflow-hidden rounded-full" role="img" :aria-label="ORDINE.map((l) => `${LIVELLI_CFD[l].breve} ${fmtPct(quote[l])}`).join(', ')">
      <div v-for="p in parti" :key="p.l" class="parte h-full" :style="{ flexGrow: p.q, background: LIVELLI_CFD[p.l].css }" />
    </div>
    <dl class="mt-2.5 grid grid-cols-3 gap-2">
      <div v-for="l in ORDINE" :key="l" class="min-w-0">
        <dt class="flex items-center gap-1.5 text-[.72rem] text-testo-3"><span class="size-2 shrink-0 rounded-full" :style="{ background: LIVELLI_CFD[l].css }" />{{ LIVELLI_CFD[l].breve }}</dt>
        <dd class="cifre m-0 mt-0.5 text-[.95rem] font-semibold">{{ fmtPct(quote[l]) }}</dd>
      </div>
    </dl>
  </div>
</template>

<style scoped>
.parte { flex-basis: 0; transition: flex-grow 600ms var(--ease-in-out); }
</style>
