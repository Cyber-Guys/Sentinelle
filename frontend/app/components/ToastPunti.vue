<script setup lang="ts">
import { Star, Trophy } from '@lucide/vue'

defineProps<{ toast: { id: number; testo: string } | null; nuovoLivello: string | null }>()
</script>

<template>
  <Transition enter-active-class="transition duration-300" enter-from-class="opacity-0 -translate-y-3" leave-active-class="transition duration-300" leave-to-class="opacity-0 -translate-y-3">
    <div v-if="toast" :key="toast.id" class="pointer-events-none fixed inset-x-0 top-16 z-50 flex justify-center">
      <span class="flex items-center gap-2 rounded-full bg-bosco px-5 py-2 text-lg font-extrabold text-white shadow-lg"><Star class="size-5" /> {{ toast.testo }}</span>
    </div>
  </Transition>
  <Transition enter-active-class="transition duration-500" enter-from-class="opacity-0 scale-75" leave-active-class="transition duration-500" leave-to-class="opacity-0">
    <div v-if="nuovoLivello" class="pointer-events-none fixed inset-0 z-[60] flex items-center justify-center bg-black/55">
      <div class="mx-6 flex flex-col items-center gap-2 rounded-3xl bg-carta px-8 py-8 text-center shadow-2xl">
        <Trophy class="size-16 text-fuoco" />
        <p class="text-sm font-semibold uppercase tracking-wide text-testo-2">Nuovo livello</p>
        <p class="text-3xl font-extrabold text-bosco">{{ nuovoLivello }}</p>
      </div>
    </div>
  </Transition>
</template>
