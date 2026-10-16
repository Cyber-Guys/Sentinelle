<script setup lang="ts">
import { Waves } from '@lucide/vue'

// Sezione "Risorse idriche" del pannello Livelli (app e cruscotto): invasi regionali con riempimento.
defineProps<{ n: number; data?: string }>()
const acceso = defineModel<boolean>({ required: true })
</script>

<template>
  <label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
    <input v-model="acceso" type="checkbox" role="switch" class="sr-only" />
    <Waves class="size-4 shrink-0 text-cielo" aria-hidden="true" />
    <span class="min-w-0 flex-1 leading-tight">
      <span class="block text-[.86rem] font-semibold">Risorse idriche</span>
      <span class="cifre block text-[.72rem] text-testo-2">{{ n }} invasi · riempimento{{ data ? ` ${data}` : '' }}</span>
    </span>
    <span class="interruttore" :class="acceso && 'acceso'" aria-hidden="true" />
  </label>
</template>
