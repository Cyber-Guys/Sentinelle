<script setup lang="ts">
import { History, House, Map as IconaMappa, User } from '@lucide/vue'

const { urgenti } = useAvvisi()
</script>

<template>
  <nav class="sezioni" aria-label="Sezioni">
    <NuxtLink to="/" class="sezione" exact-active-class="attiva"><IconaMappa aria-hidden="true" />Mappa</NuxtLink>
    <NuxtLink to="/localita" class="sezione" active-class="attiva">
      <House aria-hidden="true" />Località
      <span v-if="urgenti" class="contatore" :aria-label="`${urgenti} avvisi urgenti`">{{ urgenti }}</span>
    </NuxtLink>
    <NuxtLink to="/storico" class="sezione" active-class="attiva"><History aria-hidden="true" />Storico</NuxtLink>
    <NuxtLink to="/profilo" class="sezione" active-class="attiva"><User aria-hidden="true" />Profilo</NuxtLink>
  </nav>
</template>
