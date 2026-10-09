<script setup lang="ts">
import { Star, Trophy } from '@lucide/vue'

defineProps<{ toast: { id: number; testo: string } | null; nuovoLivello: { nome: string; punti: number } | null }>()
defineEmits<{ chiudiLivello: [] }>()
</script>

<template>
  <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="opacity-0 -translate-y-4 scale-95" leave-active-class="transition duration-200 ease-in" leave-to-class="opacity-0 -translate-y-3">
    <div v-if="toast" :key="toast.id" class="pointer-events-none fixed inset-x-0 top-24 z-50 flex justify-center" role="status">
      <span class="sospeso flex items-center gap-2.5 !rounded-full py-2 pr-5 pl-2">
        <span class="flex size-9 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb347] to-[#e8351f] shadow-[0_0_18px_rgba(255,106,43,.55)]">
          <Star class="size-[18px] fill-white text-white" aria-hidden="true" />
        </span>
        <span class="cifre text-lg font-bold">{{ toast.testo }}</span>
      </span>
    </div>
  </Transition>
  <Transition name="livello">
    <div v-if="nuovoLivello" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/55 backdrop-blur-sm" role="status" aria-live="polite" @click="$emit('chiudiLivello')">
      <div class="livello-scheda sospeso relative mx-6 flex w-full max-w-xs flex-col items-center overflow-hidden px-8 pt-9 pb-7 text-center">
                <span class="relative flex size-16 items-center justify-center">
          <span class="pulsa absolute inset-0 rounded-full ring-2 ring-[#ff8a3d]" aria-hidden="true" />
          <span class="relative flex size-16 items-center justify-center rounded-full bg-gradient-to-b from-[#f7953a] to-[#dc3a18]">
            <Trophy class="size-8 text-white" aria-hidden="true" />
          </span>
        </span>
        <p class="etichetta relative mt-5">Nuovo livello</p>
        <p class="relative mt-1 text-2xl font-semibold tracking-tight">{{ nuovoLivello.nome }}</p>
        <p v-if="nuovoLivello.punti > 0" class="cifre relative mt-3 inline-flex items-center gap-1 rounded-full bg-ambra/15 px-3 py-1 text-sm font-semibold text-ambra">
          <Star class="size-3.5 fill-current" aria-hidden="true" /> +{{ nuovoLivello.punti }} punti
        </p>
        <p class="relative mt-3 text-sm text-testo-2">La tua zona è più protetta grazie a te.</p>
        <p class="relative mt-4 text-[.72rem] text-testo-3">Tocca per continuare</p>
      </div>
    </div>
  </Transition>
</template>

<style>
.livello-enter-active { transition: opacity .3s ease-out; }
.livello-leave-active { transition: opacity .25s ease-in; }
.livello-enter-from, .livello-leave-to { opacity: 0; }
.livello-enter-active .livello-scheda { transition: transform .45s cubic-bezier(.22, 1, .36, 1); }
.livello-enter-from .livello-scheda { transform: scale(.96) translateY(8px); }
</style>
