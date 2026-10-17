<script setup lang="ts">
import { Smartphone, MonitorCog, Flame, ArrowRight } from '@lucide/vue'
</script>

<template>
  <main class="relative flex min-h-dvh flex-col px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-10">
    <div class="flex justify-end"><InterruttoreTema /></div>

    <div class="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center text-center">
      <span class="flex size-14 items-center justify-center rounded-[32%] bg-gradient-to-b from-[#f2581d] to-[#d33515] shadow-[0_8px_24px_-10px_rgba(255,90,31,.6),inset_0_1px_0_rgba(255,255,255,.2)]">
        <Flame class="size-7 text-white" aria-hidden="true" />
      </span>
      <p class="etichetta mt-6">Sardegna · prevenzione incendi</p>
      <h1 class="mt-2 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight sm:text-5xl">Sentinelle</h1>
      <p class="mt-3 max-w-md text-base text-testo-2">Segnalazione partecipata degli incendi: i cittadini vedono, gli operatori decidono prima.</p>

      <div class="mt-10 grid w-full max-w-xl gap-3 sm:grid-cols-2">
        <NuxtLink to="/app" class="vetro group flex items-center gap-3.5 p-4 text-left transition-colors hover:bg-vetro-forte">
          <span class="flex size-10 shrink-0 items-center justify-center rounded-s bg-brace/12 text-brace ring-1 ring-brace/25"><Smartphone class="size-5" aria-hidden="true" /></span>
          <span class="min-w-0 flex-1">
            <span class="block font-semibold">App cittadino</span>
            <span class="block text-[.8rem] text-testo-2">Segnala, completa missioni, scala la classifica</span>
          </span>
          <ArrowRight class="size-4 shrink-0 text-testo-3 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </NuxtLink>
        <NuxtLink to="/dashboard" class="vetro group flex items-center gap-3.5 p-4 text-left transition-colors hover:bg-vetro-forte">
          <span class="flex size-10 shrink-0 items-center justify-center rounded-s bg-cielo/12 text-cielo ring-1 ring-cielo/25"><MonitorCog class="size-5" aria-hidden="true" /></span>
          <span class="min-w-0 flex-1">
            <span class="block font-semibold">Dashboard COP</span>
            <span class="block text-[.8rem] text-testo-2">Aree COP, bollettino CFD, risorse e segnalazioni da certificare</span>
          </span>
          <ArrowRight class="size-4 shrink-0 text-testo-3 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </NuxtLink>
      </div>
    </div>
  </main>
</template>
