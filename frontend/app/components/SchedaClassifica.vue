<script setup lang="ts">
import { Crown, Star, Users, Trophy } from '@lucide/vue'

const props = defineProps<{ comune: string; nomeUtente: string }>()
const { chiama } = useApi()

const comuni = ref<RigaComune[]>([])
const utenti = ref<RigaUtente[]>([])
const errore = ref('')
const caricamento = ref(true)

async function carica() {
  caricamento.value = true; errore.value = ''
  try {
    comuni.value = await chiama<RigaComune[]>('/classifica/comuni')
    const tutti = await chiama<{ id: number; nome: string }[]>('/comuni')
    const c = tutti.find((x) => x.nome === props.comune)
    if (c) utenti.value = await chiama<RigaUtente[]>(`/classifica/utenti?comune_id=${c.id}`)
  } catch (e) { errore.value = messaggioErrore(e, 'caricare la classifica') }
  caricamento.value = false
}
onMounted(carica)

// classifica "vuota" anche quando le righe ci sono ma nessuno ha ancora punti
const senzaPunti = computed(() => !comuni.value.some((r) => r.punti > 0))

const podio = computed(() => {
  const [a, b, c] = comuni.value
  // ordine visivo: secondo, primo, terzo
  return [b && { r: b, pos: 2 }, a && { r: a, pos: 1 }, c && { r: c, pos: 3 }].filter(Boolean) as { r: RigaComune; pos: number }[]
})
const MEDAGLIA: Record<number, string> = { 1: 'var(--ambra)', 2: 'var(--testo-2)', 3: 'var(--brace)' }
const ALTEZZA: Record<number, string> = { 1: 'h-24', 2: 'h-16', 3: 'h-12' }
const nomeLivello = (l: RigaUtente['livello']) => (typeof l === 'string' ? l : l?.nome)
</script>

<template>
  <div class="space-y-6 p-3">
    <StatoErrore v-if="errore" :messaggio="errore" @riprova="carica" />
    <div v-else-if="caricamento" class="space-y-6" aria-busy="true" aria-label="Caricamento della classifica">
      <div>
        <p class="etichetta">Sfida tra comuni</p>
        <h2 class="mt-0.5 mb-4 text-lg font-semibold tracking-tight">Classifica dei comuni</h2>
        <div class="grid grid-cols-3 items-end gap-2">
          <div v-for="h in ['h-16', 'h-24', 'h-12']" :key="h" class="flex flex-col items-center gap-1.5">
            <span class="scheletro block h-3 w-14" /><span class="scheletro block h-5 w-10" />
            <span class="scheletro block w-full !rounded-m !rounded-b-s" :class="h" />
          </div>
        </div>
      </div>
      <div class="space-y-1.5"><span v-for="k in 3" :key="k" class="scheletro block h-12 w-full !rounded-m" /></div>
    </div>
    <section v-else-if="senzaPunti">
      <p class="etichetta">Sfida tra comuni</p>
      <h2 class="mt-0.5 mb-4 text-lg font-semibold tracking-tight">Classifica dei comuni</h2>
      <div class="vetro flex flex-col items-center gap-3 px-5 py-8 text-center">
      <span class="flex size-12 items-center justify-center rounded-full bg-ambra/12 text-ambra ring-1 ring-ambra/25"><Trophy class="size-6" aria-hidden="true" /></span>
      <div class="space-y-1">
        <p class="font-semibold">La sfida è appena iniziata</p>
        <p class="text-[.84rem] text-testo-2">Nessun comune ha ancora punti. Completa una missione e porta {{ nomeComune(comune) }} in testa.</p>
      </div>
      </div>
    </section>
    <template v-else>
    <section>
      <p class="etichetta">Sfida tra comuni</p>
      <h2 class="mt-0.5 mb-4 text-lg font-semibold tracking-tight">Classifica dei comuni</h2>

      <!-- podio -->
      <div v-if="podio.length" class="mb-3 grid grid-cols-3 items-end gap-2">
        <div v-for="p in podio" :key="p.r.comune" class="flex min-w-0 flex-col items-center text-center">
          <Crown v-if="p.pos === 1" class="mb-1 size-5 text-ambra" aria-hidden="true" />
          <span class="block w-full truncate text-[.82rem] font-semibold" :class="p.r.comune === comune && 'text-brace'">{{ nomeComune(p.r.comune) }}</span>
          <span class="cifre text-[1.2rem] font-semibold leading-tight">{{ p.r.punti }}</span>
          <div class="vetro mt-1.5 flex w-full items-start justify-center !rounded-b-s pt-2" :class="[ALTEZZA[p.pos], p.pos === 1 && 'bg-gradient-to-b from-ambra/12 to-transparent', p.r.comune === comune && '!border-brace/50 ring-1 ring-brace/30']">
            <span class="cifre flex size-7 items-center justify-center rounded-full text-[.85rem] font-bold text-fondo" :style="{ background: MEDAGLIA[p.pos] }">{{ p.pos }}</span>
          </div>
        </div>
      </div>

      <ol class="space-y-1.5">
        <li v-for="(r, i) in comuni.slice(3)" :key="r.comune" class="vetro flex items-center gap-3 px-3 py-2.5" :class="r.comune === comune && '!border-brace/50 bg-brace/8'">
          <span class="cifre w-6 text-center font-semibold text-testo-3">{{ i + 4 }}</span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block truncate font-semibold">{{ nomeComune(r.comune) }}</span>
            <span class="flex items-center gap-1 text-[.74rem] text-testo-2"><Users class="size-3" aria-hidden="true" /> <span class="cifre">{{ r.utenti }}</span> sentinelle</span>
          </span>
          <span v-if="r.comune === comune" class="rounded-full bg-brace/15 px-2 py-0.5 text-[.68rem] font-semibold text-brace">il tuo</span>
          <span class="cifre text-base font-semibold">{{ r.punti }}</span>
        </li>
      </ol>
    </section>

    <section>
      <p class="etichetta">Il tuo comune</p>
      <h2 class="mt-0.5 mb-3 text-lg font-semibold tracking-tight">Sentinelle di {{ nomeComune(comune) }}</h2>
      <ol class="vetro divide-y divide-bordo overflow-hidden !p-0">
        <li v-for="(u, i) in utenti" :key="u.nome" class="flex items-center gap-3 px-3 py-2.5" :class="u.nome === nomeUtente && 'bg-brace/8'">
          <span class="cifre flex size-7 shrink-0 items-center justify-center rounded-full text-[.8rem] font-bold" :class="i < 3 ? 'text-fondo' : 'text-testo-3'" :style="i < 3 ? { background: MEDAGLIA[i + 1] } : undefined">{{ i + 1 }}</span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block truncate font-semibold">{{ u.nome }}<span v-if="u.nome === nomeUtente" class="ml-1.5 text-[.7rem] font-semibold text-brace">tu</span></span>
            <span class="block text-[.74rem] text-testo-2">{{ nomeLivello(u.livello) }}</span>
          </span>
          <span class="cifre flex items-center gap-1 font-semibold"><Star class="size-3.5 fill-ambra text-ambra" aria-hidden="true" />{{ u.punti }}</span>
        </li>
        <li v-if="!utenti.length" class="px-3 py-4 text-center text-sm text-testo-2">Nessuna sentinella con punti nel tuo comune: inizia tu.</li>
      </ol>
    </section>
    </template>
  </div>
</template>
