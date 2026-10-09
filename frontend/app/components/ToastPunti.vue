<script setup lang="ts">
import { Star, Trophy } from '@lucide/vue'

defineProps<{ toast: { id: number; testo: string } | null; nuovoLivello: string | null }>()
</script>

<template>
  <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 -translate-y-4 scale-95" leave-active-class="transition duration-300" leave-to-class="opacity-0 -translate-y-3">
    <div v-if="toast" :key="toast.id" class="pointer-events-none fixed inset-x-0 top-24 z-50 flex justify-center" role="status">
      <span class="sospeso flex items-center gap-2.5 !rounded-full py-2 pr-5 pl-2">
        <span class="flex size-9 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb347] to-[#e8351f] shadow-[0_0_18px_rgba(255,106,43,.55)]">
          <Star class="size-[18px] fill-white text-white" aria-hidden="true" />
        </span>
        <span class="cifre text-lg font-bold">{{ toast.testo }}</span>
      </span>
    </div>
  </Transition>
  <Transition enter-active-class="transition duration-500 ease-out" enter-from-class="opacity-0" leave-active-class="transition duration-500" leave-to-class="opacity-0">
    <div v-if="nuovoLivello" class="pointer-events-none fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm" role="status">
      <div class="sospeso relative mx-6 flex w-full max-w-xs flex-col items-center overflow-hidden px-8 py-9 text-center">
        <div class="pointer-events-none absolute inset-x-0 -bottom-24 h-48 bg-[radial-gradient(closest-side,rgba(255,106,43,.35),transparent)]" aria-hidden="true" />
        <span class="relative flex size-20 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb347] to-[#e8351f] shadow-[0_0_40px_rgba(255,106,43,.5)]">
          <Trophy class="size-10 text-white" aria-hidden="true" />
        </span>
        <p class="etichetta relative mt-5">Nuovo livello</p>
        <p class="relative mt-1 text-3xl font-bold tracking-tight">{{ nuovoLivello }}</p>
        <p class="relative mt-2 text-sm text-testo-2">La tua zona è più protetta grazie a te.</p>
      </div>
    </div>
  </Transition>
</template>
