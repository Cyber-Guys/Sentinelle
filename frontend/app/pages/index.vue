<script setup lang="ts">
import { Smartphone, MonitorCog, Flame, ArrowRight } from '@lucide/vue'
</script>

<template>
  <main class="relative flex min-h-dvh flex-col px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-10">
    <div class="flex justify-end"><InterruttoreTema /></div>

    <div class="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center text-center">
      <span class="relative flex size-24 items-center justify-center">
        <span class="absolute inset-0 rounded-full bg-[radial-gradient(closest-side,rgba(255,106,43,.5),transparent)] blur-lg" aria-hidden="true" />
        <span class="relative flex size-[4.5rem] items-center justify-center rounded-[24px] bg-gradient-to-br from-[#ff9a3d] to-[#d92d17] shadow-[0_14px_36px_-10px_rgba(255,90,31,.65),inset_0_1px_0_rgba(255,255,255,.3)]">
          <Flame class="size-10 text-white" aria-hidden="true" />
        </span>
      </span>
      <p class="etichetta mt-6">Sardegna · prevenzione incendi</p>
      <h1 class="mt-2 font-[family-name:var(--font-display)] text-5xl font-bold tracking-tight sm:text-6xl">Sentinelle</h1>
      <p class="mt-3 max-w-md text-[1.05rem] text-testo-2">Segnalazione partecipata degli incendi: i cittadini vedono, gli operatori decidono prima.</p>

      <div class="mt-10 grid w-full gap-3 sm:grid-cols-2">
        <NuxtLink to="/app" class="vetro group relative flex items-center gap-4 overflow-hidden p-5 text-left transition-colors hover:bg-vetro-forte">
          <span class="pointer-events-none absolute -right-10 -bottom-16 size-40 rounded-full bg-[radial-gradient(closest-side,rgba(255,106,43,.28),transparent)]" aria-hidden="true" />
          <span class="relative flex size-12 shrink-0 items-center justify-center rounded-[14px] bg-gradient-to-br from-[#ff9a3d] to-[#d92d17] text-white shadow-[0_8px_20px_-6px_rgba(255,90,31,.6)]"><Smartphone class="size-6" aria-hidden="true" /></span>
          <span class="relative min-w-0 flex-1">
            <span class="block text-lg font-semibold">App cittadino</span>
            <span class="block text-[.84rem] text-testo-2">Segnala, completa missioni, scala la classifica</span>
          </span>
          <ArrowRight class="relative size-5 shrink-0 text-testo-3 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </NuxtLink>
        <NuxtLink to="/cruscotto" class="vetro group flex items-center gap-4 p-5 text-left transition-colors hover:bg-vetro-forte">
          <span class="flex size-12 shrink-0 items-center justify-center rounded-[14px] bg-vetro-forte text-cielo ring-1 ring-bordo-luce"><MonitorCog class="size-6" aria-hidden="true" /></span>
          <span class="min-w-0 flex-1">
            <span class="block text-lg font-semibold">Cruscotto operatori</span>
            <span class="block text-[.84rem] text-testo-2">Coda per priorità e mappa in tempo reale</span>
          </span>
          <ArrowRight class="size-5 shrink-0 text-testo-3 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </NuxtLink>
      </div>
    </div>
  </main>
</template>
