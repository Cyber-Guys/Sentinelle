<script setup lang="ts">
import { Star, ShieldCheck } from '@lucide/vue'
import type { Livello } from '~/composables/useApi'

const props = defineProps<{ nome: string; punti: number; livello?: Livello; affidabilita?: { valore: number; etichetta: string } }>()
// affidabilita' del cittadino (dagli esiti degli operatori): scudo + parola breve, discreto
const aff = computed(() => {
  const a = props.affidabilita
  if (!a) return null
  return a.valore >= 0.7 ? { breve: 'Affidabile', colore: 'text-macchia' } : a.valore < 0.4 ? { breve: 'In prova', colore: 'text-testo-3' } : { breve: '', colore: 'text-testo-2' }
})

// i punti contano verso il valore nuovo
const mostrati = useConteggio(() => props.punti, 700)
</script>

<template>
  <div class="flex min-w-0 items-center gap-2.5">
    <AnelloLivello :nome="nome" :progresso="livello?.progresso ?? 0" :dimensione="34" />
    <span class="min-w-0 leading-tight">
      <span class="block truncate text-[.86rem] font-semibold">{{ nome }}</span>
      <span class="flex items-center gap-1 text-[.7rem] text-testo-2">
        <span v-if="livello" class="shrink-0">{{ livello.nome }}</span>
        <span v-else class="scheletro inline-block h-2.5 w-16" aria-hidden="true" />
        <span aria-hidden="true">·</span>
        <Star class="size-3 shrink-0 fill-ambra text-ambra" aria-hidden="true" />
        <span class="cifre font-semibold text-testo">{{ mostrati }}</span>
        <template v-if="aff && affidabilita">
          <span aria-hidden="true">·</span>
          <span class="flex shrink-0 items-center gap-0.5" :class="aff.colore" :title="affidabilita.etichetta">
            <ShieldCheck class="size-3 shrink-0" aria-hidden="true" /><span v-if="aff.breve" class="hidden font-medium min-[26rem]:inline" aria-hidden="true">{{ aff.breve }}</span><span class="sr-only">{{ affidabilita.etichetta }}</span>
          </span>
        </template>
      </span>
    </span>
  </div>
</template>
