<script setup lang="ts">
// Primo avvio: nome e telefono creano il profilo (niente password in questa demo). Per le prove si puo' entrare
// con un profilo gia' esistente.
import { ChevronRight, Flame, LoaderCircle } from '@lucide/vue'

definePageMeta({ layout: 'pieno' })

const api = useApi()
const sessione = useSessione()
const toast = useToast()

const nome = ref('')
const telefono = ref('')
const invio = ref(false)
const demo = ref<{ id: number; nome: string; comune: string | null }[]>([])

onMounted(async () => {
  try { demo.value = (await api<typeof demo.value>('/utenti')).slice(0, 6) } catch { /* senza elenco non si vedono i profili demo */ }
})

async function continua() {
  if (!nome.value.trim() || invio.value) return
  invio.value = true
  try {
    const u = await api<Utente>('/utenti', { method: 'POST', body: { nome: nome.value.trim(), telefono: telefono.value.trim() || null } })
    sessione.entra(u)
    await navigateTo('/localita/nuova?tipo=casa&primo=1')
  } catch (e) {
    toast.errore(messaggioErrore(e))
  } finally {
    invio.value = false
  }
}

async function entraDemo(id: number) {
  try {
    sessione.entra(await api<Utente>(`/utenti/${id}`))
    await navigateTo('/')
  } catch (e) {
    toast.errore(messaggioErrore(e))
  }
}
</script>

<template>
  <div class="scorri px-5 pb-6 pt-10">
    <div class="flex flex-col items-center gap-3 text-center">
      <span class="grid size-20 place-items-center rounded-[1.6rem] bg-brace text-white shadow-sollevato"><Flame class="size-11" stroke-width="2.2" aria-hidden="true" /></span>
      <h1 class="titolo text-[2.1rem]">Sentinelle</h1>
      <p class="tenue max-w-[21rem] text-xl leading-snug">Occhi aperti sulla Sardegna. Segnala un incendio in pochi tocchi e ricevi gli avvisi per la tua casa e i tuoi terreni.</p>
    </div>

    <form class="mt-8 flex flex-col gap-4" @submit.prevent="continua">
      <div class="flex flex-col gap-1.5">
        <label class="etichetta-campo" for="nome">Come ti chiami?</label>
        <div class="campo"><input id="nome" v-model="nome" autocomplete="name" placeholder="Nome e cognome" maxlength="60" required></div>
      </div>
      <div class="flex flex-col gap-1.5">
        <label class="etichetta-campo" for="tel">Numero di telefono</label>
        <div class="campo"><input id="tel" v-model="telefono" type="tel" inputmode="tel" autocomplete="tel" placeholder="Per farti richiamare se serve" maxlength="24"></div>
        <p class="tenue">Lo vedono solo gli operatori, se devono chiederti un chiarimento su una segnalazione.</p>
      </div>
      <button type="submit" class="gigante mt-1" :disabled="!nome.trim() || invio">
        <LoaderCircle v-if="invio" class="gira" aria-hidden="true" />
        {{ invio ? 'Un attimo…' : 'Continua' }}
      </button>
    </form>

    <details v-if="demo.length" class="mt-8 rounded-[1.25rem] border-[1.5px] border-linea bg-carta">
      <summary class="flex min-h-14 cursor-pointer items-center px-4 text-lg font-bold">Prova con un profilo già esistente</summary>
      <ul class="border-t-[1.5px] border-linea">
        <li v-for="u in demo" :key="u.id" class="border-b-[1.5px] border-linea last:border-0">
          <button type="button" class="flex min-h-16 w-full items-center gap-3 px-4 text-left" @click="entraDemo(u.id)">
            <span class="grid size-10 place-items-center rounded-full bg-inchiostro font-extrabold text-white">{{ iniziale(u.nome) }}</span>
            <span class="flex-1"><span class="block text-lg font-bold">{{ u.nome }}</span><span v-if="u.comune" class="tenue block text-base capitalize">{{ u.comune.toLowerCase() }}</span></span>
            <ChevronRight class="size-6" aria-hidden="true" />
          </button>
        </li>
      </ul>
    </details>
  </div>
</template>
