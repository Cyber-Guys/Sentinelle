<script setup lang="ts">
// Scelta di un punto sulla mappa: il pin resta al centro, si muove la mappa. Usata in Segnala e Nuova localita'.
import type { Map as MappaLibre } from 'maplibre-gl'

const props = defineProps<{ centro: { lat: number; lon: number }; zoom?: number; icona?: TipoLocalita | TipoSegnalazione }>()
const emit = defineEmits<{ muovi: [{ lat: number; lon: number }] }>()

let m: MappaLibre | null = null

function pronta(mappa: MappaLibre) {
  m = mappa
  mappa.on('moveend', () => {
    const c = mappa.getCenter()
    emit('muovi', { lat: c.lat, lon: c.lng })
  })
  emit('muovi', props.centro)
}

function vaiA(lat: number, lon: number, zoom = 16) {
  m?.flyTo({ center: [lon, lat], zoom, duration: 700 })
}

defineExpose({ vaiA })
</script>

<template>
  <div class="relative h-full w-full">
    <MappaBase :centro="[centro.lon, centro.lat]" :zoom="zoom ?? 16" @pronta="pronta" />
    <!-- il pin sta fisso al centro: la sua punta e' il punto scelto -->
    <div class="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-full" aria-hidden="true">
      <div class="grid size-12 place-items-center rounded-full border-[3px] border-white bg-inchiostro text-white shadow-sollevato">
        <IconaTipo :tipo="icona ?? 'altro'" class="size-6" />
      </div>
      <div class="mx-auto h-3 w-1 rounded-b bg-inchiostro" />
    </div>
  </div>
</template>
