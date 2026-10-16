<script setup lang="ts">
// Avvio: profilo e avvisi (si accendono quando c'e' un profilo e si spengono quando esce).
const { id, carica } = useSessione()
const avvisi = useAvvisi()

onMounted(async () => {
  await carica()
})

watch(id, (v) => (v ? avvisi.avvia() : avvisi.ferma()), { immediate: true })
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <ToastLista />
</template>
