<script setup lang="ts">
// Il cruscotto e' diventato la dashboard COP (piano 2026-10-17-dashboard-cop): i vecchi link restano validi.
const route = useRoute()
await navigateTo({ path: '/dashboard', query: route.query }, { replace: true })
</script>

<template>
  <div />
</template>
