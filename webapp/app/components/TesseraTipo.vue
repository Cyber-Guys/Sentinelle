<script setup lang="ts">
// Tessera colorata per scegliere il tipo: l'icona e' grande, il nome sta scritto, la scelta ha spunta e anello.
import { Check } from '@lucide/vue'

withDefaults(defineProps<{ tipo: TipoSegnalazione; attiva?: boolean; piccola?: boolean; spenta?: boolean; breve?: boolean }>(), {})
</script>

<template>
  <button type="button" class="tessera" :class="[`t-${tipo}`, { 'tessera-piccola': piccola, 'tessera-spenta': spenta && !attiva }]" :aria-pressed="attiva">
    <span v-if="attiva" class="spunta"><Check aria-hidden="true" /></span>
    <IconaTipo :tipo="tipo" class="icona" />
    {{ breve ? TIPI[tipo].breve : TIPI[tipo].nome }}
  </button>
</template>
