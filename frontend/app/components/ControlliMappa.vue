<script setup lang="ts">
import type { Map as MappaLibre } from 'maplibre-gl'
import { Plus, Minus, Info } from '@lucide/vue'

// Controlli della mappa nostri (al posto di NavigationControl e AttributionControl di MapLibre):
// gruppo zoom a pillola 44 px e "i" da 36 che apre a sinistra l'attribuzione (obbligatoria per licenza).
const props = defineProps<{ mappa: MappaLibre | null }>()

const alMinimo = ref(false)
const alMassimo = ref(false)
const fonti = ref(false)

function aggiorna() {
  const m = props.mappa
  if (!m) return
  const z = m.getZoom()
  alMinimo.value = z <= m.getMinZoom() + 0.01
  alMassimo.value = z >= m.getMaxZoom() - 0.01
}
watch(() => props.mappa, (m, prima) => {
  prima?.off('zoom', aggiorna); prima?.off('resize', aggiorna)
  m?.on('zoom', aggiorna); m?.on('resize', aggiorna)
  aggiorna()
}, { immediate: true })
onBeforeUnmount(() => { props.mappa?.off('zoom', aggiorna); props.mappa?.off('resize', aggiorna) })
</script>

<template>
  <div class="flex flex-col items-center gap-[14px]">
    <div class="pillola flex w-11 flex-col overflow-hidden" role="group" aria-label="Zoom della mappa">
      <button type="button" class="flex h-11 w-full items-center justify-center transition-colors hover:bg-vetro-forte focus-visible:outline-offset-[-2px] disabled:cursor-default disabled:hover:bg-transparent" aria-label="Ingrandisci" :disabled="alMassimo" @click="mappa?.zoomIn()">
        <Plus class="size-[18px] text-testo transition-opacity" :class="alMassimo && 'opacity-35'" aria-hidden="true" />
      </button>
      <span class="mx-2 h-px bg-bordo" aria-hidden="true" />
      <button type="button" class="flex h-11 w-full items-center justify-center transition-colors hover:bg-vetro-forte focus-visible:outline-offset-[-2px] disabled:cursor-default disabled:hover:bg-transparent" aria-label="Riduci" :disabled="alMinimo" @click="mappa?.zoomOut()">
        <Minus class="size-[18px] text-testo transition-opacity" :class="alMinimo && 'opacity-35'" aria-hidden="true" />
      </button>
    </div>

    <div class="relative size-9">
      <Transition name="fonti">
        <p v-if="fonti" id="fonti-mappa" class="pillola absolute top-0 right-0 flex h-9 items-center pr-11 pl-3.5 text-[11px] whitespace-nowrap text-testo-2">
          ©&nbsp;<a href="https://openstreetmap.org/copyright" target="_blank" rel="noopener" class="underline-offset-2 hover:text-testo hover:underline">OpenStreetMap</a>
          <span class="mx-1.5 text-testo-3" aria-hidden="true">·</span>
          <a href="https://protomaps.com" target="_blank" rel="noopener" class="underline-offset-2 hover:text-testo hover:underline">Protomaps</a>
        </p>
      </Transition>
      <button
        type="button"
        class="pillola tocco relative flex size-9 items-center justify-center transition-colors hover:bg-vetro-forte"
        :class="fonti && '!border-transparent !bg-transparent !shadow-none ![backdrop-filter:none]'"
        :aria-expanded="fonti"
        aria-controls="fonti-mappa"
        :aria-label="fonti ? 'Nascondi le fonti della mappa' : 'Mostra le fonti della mappa'"
        @click="fonti = !fonti"
      >
        <Info class="size-[18px] text-testo" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<style>
.fonti-enter-active { transition: opacity .18s ease-out, clip-path .22s cubic-bezier(.22, 1, .36, 1); }
.fonti-leave-active { transition: opacity .12s ease-in, clip-path .12s ease-in; }
.fonti-enter-from, .fonti-leave-to { opacity: 0; clip-path: inset(0 0 0 calc(100% - 36px) round 999px); }
</style>
