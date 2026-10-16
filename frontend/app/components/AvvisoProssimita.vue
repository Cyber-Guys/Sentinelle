<script setup lang="ts">
import { X, ShieldCheck, Navigation2, Clock } from '@lucide/vue'

// Avviso di prossimita' "alla Waze": card dal basso, una per volta. Freccia verso la segnalazione (relativa al
// telefono se c'e' la bussola, altrimenti al nord), conto alla rovescia che chiude da solo (si ferma al tocco).
const props = defineProps<{ s: Condivisa; pos: { lat: number; lon: number } | null; inCorso: boolean; errore: string }>()
const emit = defineEmits<{ vota: [voto: 'ancora' | 'finito']; chiudi: [] }>()

const DURATA = 12000
const t = computed(() => TIPI[props.s.tipo])
const uff = computed(() => STATI_UFF[props.s.stato_ufficiale])
const sottoSoglia = computed(() => props.s.affidabilita.livello === 'da_verificare')
const dist = computed(() => (props.pos ? distanzaM(props.pos, props.s) : null))
const motivo = computed(() => {
  if (props.s.stato_ufficiale === 'spento') return 'Gli operatori l\'hanno chiusa come spenta.'
  if (dist.value === null) return 'Serve la tua posizione per confermare.'
  if (dist.value > RAGGIO_VOTO_M) return `Sei a ${distanzaTesto(dist.value)}: puoi confermare solo entro 2 km.`
  return null
})

// direzione: bearing dalla posizione GPS; con la bussola la freccia e' relativa a dove punta il telefono
const bearing = computed(() => {
  const p = props.pos
  if (!p) return 0
  const r = Math.PI / 180, f1 = p.lat * r, f2 = props.s.lat * r, dl = (props.s.lon - p.lon) * r
  const y = Math.sin(dl) * Math.cos(f2), x = Math.cos(f1) * Math.sin(f2) - Math.sin(f1) * Math.cos(f2) * Math.cos(dl)
  return (Math.atan2(y, x) / r + 360) % 360
})
const PUNTI = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest']
const cardinale = computed(() => PUNTI[Math.round(bearing.value / 45) % 8])
const rotta = ref<number | null>(null)
let giro = 0 // angolo continuo: la freccia non fa il giro lungo passando da 359 a 0
const angolo = computed(() => {
  const a = (bearing.value - (rotta.value ?? 0) + 360) % 360
  giro += ((a - giro % 360 + 540) % 360) - 180
  return giro
})
function orienta(e: DeviceOrientationEvent) {
  const w = (e as any).webkitCompassHeading as number | undefined
  if (typeof w === 'number') rotta.value = w
  else if (e.absolute && e.alpha !== null) rotta.value = (360 - e.alpha) % 360
}

// conto alla rovescia: anello attorno alla X; il tocco lo ferma, il voto lo sostituisce con la chiusura dopo l'esito
const resto = ref(DURATA)
const fermo = ref(false)
let tick: ReturnType<typeof setInterval> | undefined
let tFine: ReturnType<typeof setTimeout> | undefined
function ferma() { fermo.value = true }
watch(() => props.s.mio_voto, (v) => { if (v) { fermo.value = true; clearTimeout(tFine); tFine = setTimeout(() => emit('chiudi'), 4500) } })

onMounted(() => {
  try { navigator.vibrate?.([60, 40, 60]) } catch {}
  tick = setInterval(() => {
    if (fermo.value) return
    resto.value = Math.max(0, resto.value - 100)
    if (!resto.value) emit('chiudi')
  }, 100)
  window.addEventListener('deviceorientationabsolute', orienta as EventListener)
  window.addEventListener('deviceorientation', orienta)
})
onBeforeUnmount(() => {
  clearInterval(tick); clearTimeout(tFine)
  window.removeEventListener('deviceorientationabsolute', orienta as EventListener)
  window.removeEventListener('deviceorientation', orienta)
})
const ANELLO = 2 * Math.PI * 20
</script>

<template>
  <section class="avviso sospeso p-3.5" role="alertdialog" aria-modal="false" aria-labelledby="avviso-titolo" aria-describedby="avviso-dove" @pointerdown="ferma" @focusin="ferma">
    <div class="flex items-start gap-3.5">
      <span class="avviso-icona relative flex size-14 shrink-0 items-center justify-center rounded-full" :style="{ '--tinta': t.colore }" aria-hidden="true">
        <component :is="t.icona" class="relative size-7" />
      </span>
      <div class="min-w-0 flex-1 pt-0.5">
        <p class="etichetta flex items-center gap-1.5">
          <span class="inline-flex items-center gap-1 rounded-full px-1.5 py-px normal-case tracking-normal text-[.7rem]" :style="{ color: uff.colore, background: `color-mix(in srgb, ${uff.colore} 14%, transparent)` }"><ShieldCheck class="size-3" aria-hidden="true" />{{ uff.etichetta }}</span>
          <span class="inline-flex items-center gap-1 normal-case tracking-normal text-[.7rem] font-medium"><Clock class="size-3" aria-hidden="true" />{{ daQuanto(s.creata_il) }}</span>
        </p>
        <h2 id="avviso-titolo" class="mt-1 text-[1.08rem] leading-snug font-semibold text-balance">
          <template v-if="sottoSoglia">Qualcuno ha visto {{ t.breve }} qui vicino: lo vedi anche tu?</template>
          <template v-else>{{ t.etichetta }} segnalat{{ s.tipo === 'area_a_rischio' ? 'a' : 'o' }} vicino a te</template>
        </h2>
      </div>
      <button type="button" class="tocco relative -mt-1 -mr-1 flex size-11 shrink-0 items-center justify-center rounded-full text-testo-2 transition-colors hover:bg-vetro-forte hover:text-testo" :aria-label="fermo ? 'Ignora' : `Ignora (si chiude tra ${Math.ceil(resto / 1000)} secondi)`" @click="$emit('chiudi')">
        <svg v-if="!fermo" class="absolute inset-0 size-11 -rotate-90" viewBox="0 0 44 44" aria-hidden="true">
          <circle cx="22" cy="22" r="20" fill="none" stroke="var(--bordo-luce)" stroke-width="2" />
          <circle cx="22" cy="22" r="20" fill="none" stroke="var(--testo-2)" stroke-width="2" stroke-linecap="round" :stroke-dasharray="ANELLO" :stroke-dashoffset="ANELLO * (1 - resto / DURATA)" />
        </svg>
        <X class="size-4" aria-hidden="true" />
      </button>
    </div>

    <div id="avviso-dove" class="mt-3 flex items-center gap-3 rounded-m bg-vetro-forte px-3 py-2">
      <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-fondo-3 ring-1 ring-bordo-luce" aria-hidden="true">
        <Navigation2 class="freccia size-[18px]" fill="currentColor" :style="{ rotate: `${angolo}deg`, color: t.colore }" />
      </span>
      <p class="min-w-0 text-[.86rem] leading-snug">
        <span class="cifre text-[1.05rem] font-semibold">{{ dist !== null ? distanzaTesto(dist) : '—' }}</span>
        <span class="text-testo-2">&nbsp;{{ rotta !== null ? 'nella direzione della freccia' : `a ${cardinale}` }}</span>
      </p>
    </div>

    <VotoCondivisa class="mt-3" grande :s="s" :motivo="motivo" :in-corso="inCorso" :errore="errore" @vota="$emit('vota', $event)" />
    <button v-if="!s.mio_voto" type="button" class="tocco mx-auto mt-1 flex h-10 items-center px-4 text-[.82rem] font-medium text-testo-3 hover:text-testo" @click="$emit('chiudi')">Ignora</button>
  </section>
</template>

<style>
.avviso-icona { color: var(--tinta); background: color-mix(in srgb, var(--tinta) 16%, var(--fondo-3)); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--tinta) 40%, transparent); }
.avviso-icona::before, .avviso-icona::after { content: ''; position: absolute; inset: 0; border-radius: 999px; border: 1.5px solid var(--tinta); animation: avviso-onda 2.4s cubic-bezier(.2, .6, .4, 1) infinite; }
.avviso-icona::after { animation-delay: 1.2s; }
@keyframes avviso-onda { from { scale: 1; opacity: .6; } to { scale: 1.75; opacity: 0; } }
.freccia { transition: rotate .45s cubic-bezier(.22, 1, .36, 1); }
.avviso-entra-enter-active { transition: opacity .2s ease-out, transform .55s cubic-bezier(.34, 1.4, .64, 1); }
.avviso-entra-leave-active { transition: opacity .16s ease-in, transform .16s ease-in; }
.avviso-entra-enter-from { opacity: 0; transform: translateY(110%); }
.avviso-entra-leave-to { opacity: 0; transform: translateY(24px); }
@media (prefers-reduced-motion: reduce) {
  .avviso-icona::before, .avviso-icona::after { animation: none; opacity: .3; scale: 1.25; }
}
</style>
