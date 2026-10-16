<script setup lang="ts">
import { Cloud, Flame, Grape, House, MapPin, TriangleAlert } from '@lucide/vue'

defineProps<{ tipo: TipoSegnalazione | TipoLocalita | 'rischio' }>()
</script>

<template>
  <Flame v-if="tipo === 'fuoco'" aria-hidden="true" />
  <Cloud v-else-if="tipo === 'fumo'" aria-hidden="true" />
  <IconaTerreno v-else-if="tipo === 'area_a_rischio' || tipo === 'terreno'" />
  <House v-else-if="tipo === 'casa'" aria-hidden="true" />
  <Grape v-else-if="tipo === 'vigna'" aria-hidden="true" />
  <TriangleAlert v-else-if="tipo === 'rischio'" aria-hidden="true" />
  <MapPin v-else aria-hidden="true" />
</template>
