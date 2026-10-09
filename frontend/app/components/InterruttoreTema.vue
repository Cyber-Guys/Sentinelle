<script setup lang="ts">
import { Moon, Sun } from '@lucide/vue'

defineProps<{ compatto?: boolean }>()
const { tema, alterna } = useTema()
</script>

<template>
  <button
    v-if="compatto"
    type="button"
    class="pillola flex size-11 shrink-0 items-center justify-center transition-colors hover:bg-vetro-forte"
    :aria-label="tema === 'scuro' ? 'Tema scuro attivo: passa al chiaro' : 'Tema chiaro attivo: passa allo scuro'"
    @click="alterna"
  >
    <Moon v-if="tema === 'scuro'" class="size-[18px] text-ambra" aria-hidden="true" />
    <Sun v-else class="size-[18px] text-brace" aria-hidden="true" />
  </button>
  <button
    v-else
    type="button"
    class="pillola relative flex h-10 w-[4.25rem] shrink-0 items-center p-1"
    role="switch"
    :aria-checked="tema === 'chiaro'"
    :aria-label="tema === 'scuro' ? 'Tema scuro attivo: passa al chiaro' : 'Tema chiaro attivo: passa allo scuro'"
    @click="alterna"
  >
    <span
      class="absolute top-1 size-8 rounded-full bg-vetro-forte shadow-[0_2px_8px_-2px_rgba(0,0,0,.4)] ring-1 ring-bordo-luce transition-[left] duration-200"
      :class="tema === 'scuro' ? 'left-1' : 'left-[calc(100%-2.25rem)]'"
      aria-hidden="true"
    />
    <span class="relative z-10 flex w-full justify-between px-[7px]" aria-hidden="true">
      <Moon class="size-[18px] transition-colors" :class="tema === 'scuro' ? 'text-ambra' : 'text-testo-3'" />
      <Sun class="size-[18px] transition-colors" :class="tema === 'chiaro' ? 'text-brace' : 'text-testo-3'" />
    </span>
  </button>
</template>
