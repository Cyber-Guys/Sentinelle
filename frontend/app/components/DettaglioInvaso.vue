<script setup lang="ts">
// Corpo del popup di un invaso (dentro PopupMappa): riempimento con barra, volumi, data e fonte del dato.
const p = defineProps<{ riempimento: number; volume: number; capacita: number; data: string; fonte: string }>()
const mese = computed(() => { const [a, m] = p.data.split('-'); return new Date(Number(a), Number(m) - 1).toLocaleDateString('it-IT', { month: 'long', year: 'numeric' }) })
const n = (v: number) => v.toLocaleString('it-IT', { maximumFractionDigits: v < 10 ? 2 : 1 })
</script>

<template>
  <div class="mt-2.5">
    <div class="flex items-baseline justify-between text-[.8rem]"><span class="text-testo-2">Riempimento</span><span class="cifre font-semibold text-cielo">{{ riempimento }}%</span></div>
    <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-vetro-forte" role="meter" :aria-valuenow="riempimento" aria-valuemin="0" aria-valuemax="100" aria-label="Riempimento"><div class="h-full rounded-full bg-cielo" :style="{ width: `${Math.min(100, riempimento)}%` }" /></div>
    <p class="cifre mt-1.5 text-[.8rem] text-testo-2">{{ n(volume) }} di {{ n(capacita) }} milioni di m³</p>
    <p class="mt-2.5 border-t border-bordo pt-2 text-[.72rem] leading-snug text-testo-3">Dato di {{ mese }} · {{ fonte }}</p>
  </div>
</template>
