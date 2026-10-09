<script setup lang="ts">
import { Smartphone, MonitorCog, Flame } from '@lucide/vue'
</script>

<template>
  <main class="min-h-screen flex flex-col items-center justify-center gap-6 p-6">
    <h1 class="flex items-center gap-2 text-4xl font-extrabold text-fuoco"><Flame class="size-9" /> Sentinelle</h1>
    <p class="text-testo-2 text-center max-w-md">Segnalazione partecipata degli incendi in Sardegna.</p>
    <div class="grid gap-4 w-full max-w-xl sm:grid-cols-2">
      <NuxtLink to="/app" class="primario flex flex-col items-center gap-2 p-8 text-xl"><Smartphone class="size-10" /> App cittadino</NuxtLink>
      <NuxtLink to="/cruscotto" class="secondario flex flex-col items-center gap-2 p-8 text-xl"><MonitorCog class="size-10" /> Cruscotto operatori</NuxtLink>
    </div>
  </main>
</template>
