<script setup lang="ts">
// Mappa MapLibre con la base offline e, a richiesta, il satellite. Il genitore riceve la mappa con `pronta`
// (stile gia' caricato). Nessun controllo di MapLibre (scala, fonti, zoom): i crediti stanno nel Profilo.
import maplibregl, { type Map as MappaLibre } from 'maplibre-gl'

const props = withDefaults(defineProps<{ centro: [number, number]; zoom?: number; interattiva?: boolean; limiti?: boolean; vista?: Vista }>(), {
  zoom: 14, interattiva: true, limiti: true, vista: 'mappa',
})
const emit = defineEmits<{ pronta: [MappaLibre]; satelliteKo: [] }>()

const el = ref<HTMLDivElement>()
const mappa = shallowRef<MappaLibre>()
let osservatore: ResizeObserver | null = null
let erroriSatellite = 0

onMounted(() => {
  registraPmtiles()
  const m = new maplibregl.Map({
    container: el.value!, style: stileMappa(props.vista), center: props.centro, zoom: props.zoom,
    minZoom: 5.5, maxZoom: 19, interactive: props.interattiva, attributionControl: false, dragRotate: false,
    pitchWithRotate: false, locale: LOCALE_MAPPA, fadeDuration: 150, maxBounds: props.limiti ? LIMITI : undefined,
  })
  m.touchZoomRotate.disableRotation()
  mappa.value = m
  m.once('load', () => emit('pronta', m))
  // satellite irraggiungibile (niente rete): il genitore torna alla mappa normale
  m.on('error', (e: any) => {
    if (e?.sourceId === 'satellite' && props.vista === 'satellite' && ++erroriSatellite === 4) emit('satelliteKo')
  })
  osservatore = new ResizeObserver(() => m.resize())
  osservatore.observe(el.value!)
})

watch(() => props.vista, (v) => { if (mappa.value) { erroriSatellite = 0; impostaVista(mappa.value, v) } })

onBeforeUnmount(() => {
  osservatore?.disconnect()
  mappa.value?.remove()
})

defineExpose({ mappa })
</script>

<template>
  <div ref="el" class="mappa-contenitore h-full w-full" role="region" aria-label="Mappa" />
</template>
