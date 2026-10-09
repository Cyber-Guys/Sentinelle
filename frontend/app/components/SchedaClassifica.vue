<script setup lang="ts">
const props = defineProps<{ comune: string; nomeUtente: string }>()
const { chiama } = useApi()

const comuni = ref<RigaComune[]>([])
const utenti = ref<RigaUtente[]>([])
const errore = ref('')

onMounted(async () => {
  try {
    comuni.value = await chiama<RigaComune[]>('/classifica/comuni')
    const tutti = await chiama<{ id: number; nome: string }[]>('/comuni')
    const c = tutti.find((x) => x.nome === props.comune)
    if (c) utenti.value = await chiama<RigaUtente[]>(`/classifica/utenti?comune_id=${c.id}`)
  } catch (e: any) { errore.value = 'Classifica non disponibile: ' + e.message }
})

const nomeLivello = (l: RigaUtente['livello']) => (typeof l === 'string' ? l : l?.nome)
</script>

<template>
  <div class="space-y-5 p-4">
    <p v-if="errore" class="text-sm text-alta">{{ errore }}</p>
    <section>
      <h2 class="mb-2 text-lg font-bold">Classifica dei comuni</h2>
      <ol class="space-y-1.5">
        <li v-for="(r, i) in comuni" :key="r.comune" class="flex items-center gap-3 rounded-xl border p-3" :class="r.comune === comune ? 'border-fuoco bg-orange-50' : 'border-bordo bg-carta'">
          <span class="flex size-8 shrink-0 items-center justify-center rounded-full bg-bosco-chiaro font-extrabold text-bosco">{{ i + 1 }}</span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold"><span class="capitalize">{{ r.comune.toLowerCase() }}</span><span v-if="r.comune === comune" class="ml-1 text-xs font-bold text-fuoco">il tuo comune</span></span>
            <span class="block text-xs text-testo-2">{{ r.utenti }} utenti attivi</span>
          </span>
          <span class="font-extrabold text-bosco">{{ r.punti }}</span>
        </li>
        <li v-if="!comuni.length && !errore" class="text-sm text-testo-2">Ancora nessun punto assegnato.</li>
      </ol>
    </section>
    <section>
      <h2 class="mb-2 text-lg font-bold">Sentinelle di <span class="capitalize">{{ comune.toLowerCase() }}</span></h2>
      <ol class="space-y-1.5">
        <li v-for="(u, i) in utenti" :key="u.nome" class="flex items-center gap-3 rounded-xl border p-3" :class="u.nome === nomeUtente ? 'border-fuoco bg-orange-50' : 'border-bordo bg-carta'">
          <span class="w-6 text-center font-bold text-testo-2">{{ i + 1 }}</span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-semibold">{{ u.nome }}</span>
            <span class="block text-xs text-testo-2">{{ nomeLivello(u.livello) }}</span>
          </span>
          <span class="font-bold text-bosco">{{ u.punti }}</span>
        </li>
      </ol>
    </section>
  </div>
</template>
