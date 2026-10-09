<script setup lang="ts">
import { Star } from '@lucide/vue'
import type { Livello } from '~/composables/useApi'

const props = defineProps<{ nome: string; punti: number; livello?: Livello }>()

// i punti contano verso il valore nuovo
const mostrati = useConteggio(() => props.punti, 700)
</script>

<template>
  <div class="flex min-w-0 items-center gap-2.5">
    <AnelloLivello :nome="nome" :progresso="livello?.progresso ?? 0" :dimensione="40" />
    <span class="min-w-0 leading-tight">
      <span class="block truncate text-[.92rem] font-semibold">{{ nome }}</span>
      <span class="flex items-center gap-1 text-[.72rem] text-testo-2">
        <span v-if="livello" class="truncate">{{ livello.nome }}</span>
        <span v-else class="scheletro inline-block h-2.5 w-16" aria-hidden="true" />
        <span aria-hidden="true">·</span>
        <Star class="size-3 shrink-0 fill-ambra text-ambra" aria-hidden="true" />
        <span class="cifre font-semibold text-testo">{{ mostrati }}</span>
      </span>
    </span>
  </div>
</template>
