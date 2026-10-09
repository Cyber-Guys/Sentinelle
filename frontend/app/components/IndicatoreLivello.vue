<script setup lang="ts">
import { Star } from '@lucide/vue'
import type { Livello } from '~/composables/useApi'

const props = defineProps<{ nome: string; punti: number; livello?: Livello }>()

// i punti contano verso il valore nuovo
const mostrati = ref(props.punti)
let raf = 0
watch(() => props.punti, (nuovo, vecchio) => {
  cancelAnimationFrame(raf)
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { mostrati.value = nuovo; return }
  const t0 = performance.now(), da = vecchio ?? 0
  const passo = (t: number) => {
    const k = Math.min(1, (t - t0) / 700)
    mostrati.value = Math.round(da + (nuovo - da) * (1 - Math.pow(1 - k, 3)))
    if (k < 1) raf = requestAnimationFrame(passo)
  }
  raf = requestAnimationFrame(passo)
})
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <div class="flex min-w-0 items-center gap-2.5">
    <AnelloLivello :nome="nome" :progresso="livello?.progresso ?? 0" :dimensione="40" />
    <span class="min-w-0 leading-tight">
      <span class="block truncate text-[.92rem] font-semibold">{{ nome }}</span>
      <span class="flex items-center gap-1 text-[.72rem] text-testo-2">
        <span class="truncate">{{ livello?.nome ?? 'Osservatore' }}</span>
        <span aria-hidden="true">·</span>
        <Star class="size-3 shrink-0 fill-ambra text-ambra" aria-hidden="true" />
        <span class="cifre font-semibold text-testo">{{ mostrati }}</span>
      </span>
    </span>
  </div>
</template>
