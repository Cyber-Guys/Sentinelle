<script setup lang="ts">
// Incendi per mese: stagione 2025 (barre, brace) contro la media 2015-2024 (linea neutra). Un solo asse.
const props = defineProps<{ anno: number[]; media: number[] }>()
const MESI = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
const L = 336, A = 150, SX = 26, DX = 4, ALTO = 8, BASSO = 20
const lw = (L - SX - DX) / 12
const max = computed(() => {
  const m = Math.max(...props.anno, ...props.media, 1)
  const passo = m > 150 ? 50 : m > 60 ? 25 : m > 20 ? 10 : 5
  return Math.ceil(m / passo) * passo
})
const y = (v: number) => A - BASSO - (v / max.value) * (A - BASSO - ALTO)
const griglia = computed(() => [0, max.value / 2, max.value])
const linea = computed(() => props.media.map((v, i) => `${i ? 'L' : 'M'}${SX + lw * i + lw / 2},${y(v)}`).join(' '))
// barra con estremo dati arrotondato (4 px) e base piatta sull'asse
function barra(i: number, v: number) {
  const x = SX + lw * i + 3, w = lw - 6, top = y(v), base = y(0), r = Math.min(4, (base - top) / 2, w / 2)
  if (base - top < 0.5) return ''
  return `M${x},${base} V${top + r} Q${x},${top} ${x + r},${top} H${x + w - r} Q${x + w},${top} ${x + w},${top + r} V${base} Z`
}
const sopra = ref<number | null>(null)
const picco = computed(() => props.anno.indexOf(Math.max(...props.anno)))
</script>

<template>
  <figure class="m-0">
    <div class="mb-2 flex items-center gap-4 text-[.74rem] text-testo-2">
      <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-[3px] bg-brace" />Stagione 2025</span>
      <span class="flex items-center gap-1.5"><span class="h-0.5 w-3.5 rounded-full bg-testo-3" />Media 2015-2024</span>
    </div>
    <div class="relative">
      <svg :viewBox="`0 0 ${L} ${A}`" class="block w-full overflow-visible" role="img"
        :aria-label="`Incendi per mese nella stagione 2025: picco a ${MESI[picco]} con ${anno[picco]} incendi`" @mouseleave="sopra = null">
        <g class="text-testo-3">
          <template v-for="g in griglia" :key="g">
            <line :x1="SX" :x2="L - DX" :y1="y(g)" :y2="y(g)" stroke="currentColor" :stroke-opacity="g === 0 ? 0.5 : 0.18" stroke-width="1" />
            <text :x="SX - 6" :y="y(g) + 3.5" text-anchor="end" class="cifre fill-current text-[9.5px]">{{ g }}</text>
          </template>
        </g>
        <rect v-if="sopra != null" :x="SX + lw * sopra" :y="ALTO - 4" :width="lw" :height="A - BASSO - ALTO + 4" rx="4" class="fill-testo/[.06]" />
        <path v-for="(v, i) in anno" :key="i" :d="barra(i, v)" class="barra fill-brace" :style="{ '--i': i }" :fill-opacity="sopra == null || sopra === i ? 0.9 : 0.45" />
        <path :d="linea" fill="none" class="stroke-testo-2" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        <circle v-for="(v, i) in media" :key="`m${i}`" :cx="SX + lw * i + lw / 2" :cy="y(v)" :r="sopra === i ? 4.5 : 2.5" class="fill-testo-2 stroke-fondo-2" stroke-width="2" />
        <text v-for="(m, i) in MESI" :key="m" :x="SX + lw * i + lw / 2" :y="A - 5" text-anchor="middle" class="text-[9.5px]" :class="sopra === i ? 'fill-testo' : 'fill-testo-3'">{{ m[0] }}</text>
        <!-- aree di aggancio piu' larghe delle barre -->
        <rect v-for="(m, i) in MESI" :key="`h${m}`" :x="SX + lw * i" y="0" :width="lw" :height="A" fill="transparent" @mouseenter="sopra = i" />
      </svg>
      <div v-if="sopra != null" class="suggerimento pointer-events-none absolute top-0 z-10 rounded-m px-2.5 py-2 text-[.74rem]"
        :style="{ left: `${((SX + lw * sopra + lw / 2) / L) * 100}%`, translate: sopra > 7 ? '-100% 0' : sopra < 3 ? '0 0' : '-50% 0' }">
        <p class="font-semibold">{{ MESI[sopra] }}</p>
        <p class="cifre text-testo-2"><span class="text-testo">{{ anno[sopra] }}</span> nel 2025 · media {{ media[sopra]!.toLocaleString('it-IT') }}</p>
      </div>
    </div>
  </figure>
</template>

<style scoped>
.barra { transform-box: fill-box; transform-origin: bottom; animation: cresce 520ms var(--ease-out) both; animation-delay: calc(var(--i) * 22ms); transition: fill-opacity 150ms ease; }
@keyframes cresce { from { transform: scaleY(0.2); opacity: 0; } }
.suggerimento { background: var(--fondo-3); border: 1px solid var(--bordo-luce); box-shadow: var(--ombra); white-space: nowrap; }
</style>
