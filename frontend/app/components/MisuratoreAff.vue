<script setup lang="ts">
// Misuratore di affidabilita' (avviso di prossimita' e popup): barra a tre tratti con le soglie del backend
// (pesi.toml: probabile 1,0 · comunita' 2,5), riempimento che avanza col valore nuovo dopo un voto.
const props = defineProps<{ valore: number; livello: LivelloAff }>()
const MAX = 3.5
const SOGLIE = [
  { da: 0, a: 1, etichetta: 'Da verificare', liv: 'da_verificare' },
  { da: 1, a: 2.5, etichetta: 'Probabile', liv: 'probabile' },
  { da: 2.5, a: MAX, etichetta: 'Comunità', liv: 'comunita' },
] as const
const pieno = computed(() => (props.livello === 'operatori' ? 100 : Math.min(100, Math.max(4, (props.valore / MAX) * 100))))
const colore = computed(() => LIVELLI_AFF[props.livello].colore)
const attivo = (liv: string) => liv === props.livello || (props.livello === 'operatori' && liv === 'comunita')
</script>

<template>
  <div class="misuratore" role="meter" :aria-valuenow="valore" aria-valuemin="0" :aria-valuemax="MAX" :aria-valuetext="LIVELLI_AFF[livello].etichetta">
    <div class="relative h-1.5 overflow-hidden rounded-full bg-vetro-forte">
      <span class="absolute inset-y-0 left-0 rounded-full transition-[width,background-color] duration-700 ease-out" :style="{ width: `${pieno}%`, background: colore, boxShadow: `0 0 10px ${colore}` }" />
      <span v-for="s in SOGLIE.slice(1)" :key="s.liv" class="absolute inset-y-0 w-0.5 bg-fondo" :style="{ left: `${(s.da / MAX) * 100}%` }" aria-hidden="true" />
    </div>
    <div class="mt-1 flex text-[.68rem] leading-tight" aria-hidden="true">
      <span v-for="s in SOGLIE" :key="s.liv" class="truncate transition-colors" :style="{ width: `${((s.a - s.da) / MAX) * 100}%`, color: attivo(s.liv) ? colore : undefined }" :class="attivo(s.liv) ? 'font-semibold' : 'text-testo-3'">{{ s.etichetta }}</span>
    </div>
  </div>
</template>
