<script setup lang="ts">
import { X } from '@lucide/vue'
import type { Component } from 'vue'

// Guscio comune dei popup sulla mappa (storico nell'app, mappature nel cruscotto): montato da `apriPopup()`.
defineProps<{
  icona: Component
  tinta: readonly [string, string] // [scuro, chiaro]: colore dell'icona coerente coi layer della mappa
  etichetta: string
  titolo: string
  sottotitolo?: string
}>()
defineEmits<{ chiudi: [] }>()
</script>

<template>
  <article class="popup-mappa" :style="{ '--tinta-scuro': tinta[0], '--tinta-chiaro': tinta[1] }">
    <header class="flex items-center gap-2">
      <span class="popup-icona flex size-6 shrink-0 items-center justify-center rounded-s" aria-hidden="true">
        <component :is="icona" class="size-3.5" />
      </span>
      <span class="etichetta min-w-0 flex-1 truncate">{{ etichetta }}</span>
      <button type="button" aria-label="Chiudi" class="popup-chiudi tocco -mr-1 flex size-7 shrink-0 items-center justify-center rounded-full text-testo-3 transition-colors hover:bg-vetro-forte hover:text-testo" @click="$emit('chiudi')">
        <X class="size-3.5" aria-hidden="true" />
      </button>
    </header>
    <h3 class="mt-2 text-[.95rem] leading-snug font-semibold">{{ titolo }}</h3>
    <p v-if="sottotitolo" class="text-[.8rem] leading-snug text-testo-2">{{ sottotitolo }}</p>
    <slot />
  </article>
</template>
