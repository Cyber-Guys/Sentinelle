<script setup lang="ts">
// Nuova localita': si cerca un indirizzo, o si sceglie sulla mappa (il pin resta al centro), poi tipo e nome.
import { ChevronLeft, LoaderCircle, LocateFixed, MapPin, Mic, Search } from '@lucide/vue'

definePageMeta({ layout: 'pieno' })

const route = useRoute()
const api = useApi()
const { id } = useSessione()
const { pos, reale } = usePosizione()
const toast = useToast()

const primo = route.query.primo === '1'
const tipo = ref<TipoLocalita>((['casa', 'terreno', 'vigna', 'altro'] as const).find((t) => t === route.query.tipo) ?? 'casa')
const nome = ref('')
const nomeManuale = ref(false)
const testo = ref('')
const risultati = ref<Risultato[]>([])
const cercando = ref(false)
const punto = ref({ lat: pos.value.lat, lon: pos.value.lon })
const via = ref<{ comune: string | null; indirizzo: string | null } | null>(null)
const esistenti = ref<Localita[]>([])
const modoMappa = ref(false)
const invio = ref(false)
const selettore = ref<{ vaiA: (lat: number, lon: number, zoom?: number) => void } | null>(null)

// nome suggerito: "Casa", poi "Terreno", "Terreno 2"...
const suggerito = computed(() => {
  const n = esistenti.value.filter((x) => x.tipo === tipo.value).length
  return n ? `${TIPI_LOCALITA[tipo.value]} ${n + 1}` : TIPI_LOCALITA[tipo.value]
})
watch([suggerito], () => { if (!nomeManuale.value) nome.value = suggerito.value }, { immediate: true })

onMounted(async () => {
  try { esistenti.value = await api<Localita[]>(`/utenti/${id.value}/localita`) } catch { /* il nome resta quello base */ }
})

// ricerca per indirizzo
let ritardo: ReturnType<typeof setTimeout>
let salta = false
watch(testo, (q) => {
  clearTimeout(ritardo)
  if (salta) { salta = false; return }
  if (q.trim().length < 3) { risultati.value = []; return }
  ritardo = setTimeout(async () => {
    cercando.value = true
    try { risultati.value = await api<Risultato[]>('/cerca', { query: { q } }) } catch { risultati.value = [] } finally { cercando.value = false }
  }, 450)
})

function scegliRisultato(r: Risultato) {
  salta = true
  testo.value = r.nome
  risultati.value = []
  selettore.value?.vaiA(r.lat, r.lon, r.approssimato ? 14 : 17)
}

function doveSono() {
  if (!reale.value) toast.errore('Non vedo dove sei: sposta la mappa fino al punto giusto.')
  selettore.value?.vaiA(pos.value.lat, pos.value.lon)
}

// punto scelto -> via e comune (a mappa ferma)
let attesaVia: ReturnType<typeof setTimeout>
function muovi(p: { lat: number; lon: number }) {
  punto.value = p
  clearTimeout(attesaVia)
  attesaVia = setTimeout(async () => {
    try { via.value = await api<NonNullable<typeof via.value>>('/luogo', { query: p }) } catch { via.value = null }
  }, 500)
}

const indirizzo = computed(() => [via.value?.indirizzo, via.value?.comune].filter(Boolean).join(', '))

const Riconoscimento = import.meta.client ? (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition : null
function parla() {
  const r = new Riconoscimento()
  r.lang = 'it-IT'
  r.onresult = (e: any) => { testo.value = e.results[0][0].transcript }
  r.onerror = () => toast.errore('Non ho sentito bene. Riprova.')
  r.start()
}

async function salva() {
  if (invio.value || !nome.value.trim()) return
  invio.value = true
  try {
    await api(`/utenti/${id.value}/localita`, {
      method: 'POST',
      body: { nome: nome.value.trim(), tipo: tipo.value, indirizzo: indirizzo.value || null, lat: punto.value.lat, lon: punto.value.lon },
    })
    toast.ok('Località salvata')
    await navigateTo(primo ? '/' : '/localita')
  } catch (e) {
    toast.errore(messaggioErrore(e))
  } finally {
    invio.value = false
  }
}
</script>

<template>
  <div class="scorri flex flex-col gap-2.5 px-4 pb-3 pt-3">
    <div class="flex items-center gap-3">
      <NuxtLink v-if="!primo" to="/localita" class="indietro"><ChevronLeft class="size-6" aria-hidden="true" />Indietro</NuxtLink>
      <h1 class="titolo flex-1 text-[1.6rem]">{{ primo ? 'Dov’è casa tua?' : 'Nuova località' }}</h1>
      <NuxtLink v-if="primo" to="/" class="pulsante pulsante-fantasma">Salta</NuxtLink>
    </div>
    <p v-if="primo" class="tenue -mt-1 text-lg">Ti avvisiamo se c’è fumo o fuoco vicino. Puoi aggiungere anche terreni e vigne.</p>

    <label class="etichetta-campo mt-1" for="cerca">Dove si trova?</label>
    <div class="relative">
      <div class="campo">
        <Search class="size-5 flex-none" aria-hidden="true" />
        <input id="cerca" v-model="testo" type="search" autocomplete="off" placeholder="Cerca un indirizzo o una zona" enterkeyhint="search">
        <LoaderCircle v-if="cercando" class="gira size-5 flex-none" aria-hidden="true" />
        <button v-if="Riconoscimento" type="button" class="tondo !size-11 !shadow-none" aria-label="Detta a voce" @click="parla"><Mic aria-hidden="true" /></button>
      </div>
      <ul v-if="risultati.length" class="elenco absolute inset-x-0 top-full z-20 mt-1 shadow-sollevato" role="listbox" aria-label="Risultati">
        <li v-for="r in risultati" :key="r.nome + r.lat" class="riga !min-h-14 !p-0">
          <button type="button" class="flex min-h-14 w-full items-center gap-2 px-3 text-left text-base font-semibold" role="option" @click="scegliRisultato(r)">
            <MapPin class="size-5 flex-none" aria-hidden="true" />{{ r.nome }}
          </button>
        </li>
      </ul>
    </div>

    <div class="flex gap-2">
      <button type="button" class="pulsante flex-1 !px-2" @click="doveSono"><LocateFixed aria-hidden="true" />Dove sono ora</button>
      <button type="button" class="pulsante flex-1 !px-2" :class="modoMappa ? 'pulsante-scuro' : ''" :aria-pressed="modoMappa" @click="modoMappa = !modoMappa"><MapPin aria-hidden="true" />Sulla mappa</button>
    </div>

    <div class="relative h-[13.5rem] flex-none overflow-hidden rounded-3xl border-[1.5px] border-linea">
      <MappaPunto ref="selettore" :centro="punto" :icona="tipo" @muovi="muovi" />
      <span class="etichetta pointer-events-none absolute inset-x-0 top-2.5 mx-auto w-fit bg-white shadow-leggero">Muovi la mappa: il pin resta al centro</span>
    </div>
    <p class="min-h-6 text-base font-bold leading-tight"><MapPin class="mr-1 inline size-4 align-[-2px]" aria-hidden="true" />{{ indirizzo || 'Sposta la mappa sul punto giusto' }}</p>

    <h2 class="etichetta-campo">Che luogo è?</h2>
    <div class="flex flex-wrap gap-2" role="group" aria-label="Tipo di luogo">
      <button v-for="(t, k) in TIPI_LOCALITA" :key="k" type="button" class="scelta" :aria-pressed="tipo === k" @click="tipo = k as TipoLocalita">{{ t }}</button>
    </div>

    <label class="etichetta-campo" for="nome">Come lo chiamiamo?</label>
    <div class="campo"><input id="nome" v-model="nome" maxlength="40" @input="nomeManuale = true"></div>
  </div>

  <div class="flex-none border-t-[1.5px] border-linea bg-carta px-4 pb-4 pt-3">
    <button type="button" class="gigante !min-h-[4.5rem] !text-[1.4rem]" :disabled="invio || !nome.trim()" @click="salva">
      <LoaderCircle v-if="invio" class="gira" aria-hidden="true" />
      {{ invio ? 'Salvo…' : 'Salva località' }}
    </button>
  </div>
</template>
