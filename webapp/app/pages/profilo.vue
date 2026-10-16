<script setup lang="ts">
// Profilo: nome, telefono, segnalazioni fatte, luoghi che controllo, testo grande, notifiche.
import type { Map as MappaLibre, Marker } from 'maplibre-gl'
import { Bell, LogOut } from '@lucide/vue'

const api = useApi()
const sessione = useSessione()
const avvisi = useAvvisi()
const toast = useToast()
const { utente } = sessione

const luoghi = ref<Localita[]>([])
const apertoModifica = ref(false)
const nomeM = ref('')
const telM = ref('')
const salvando = ref(false)
let pin: Marker[] = []

onMounted(async () => {
  avvisi.leggiPermesso()
  sessione.carica()
  try { luoghi.value = await api<Localita[]>(`/utenti/${sessione.id.value}/localita`) } catch { /* senza elenco resta la mappa vuota */ }
})
onBeforeUnmount(() => pin.forEach((p) => p.remove()))

function pronta(m: MappaLibre) {
  pin.forEach((p) => p.remove())
  pin = luoghi.value.map((l) => mettiPin(m, l.lat, l.lon, { icona: l.tipo, classe: `pin-piccolo pin-l-${l.stato.livello.split(' ')[0]}` }))
  inquadra(m, luoghi.value, { margine: 28, zoomMax: 12 })
}

function apriModifica() {
  nomeM.value = utente.value?.nome ?? ''
  telM.value = utente.value?.telefono ?? ''
  apertoModifica.value = true
}

async function salvaProfilo() {
  if (!nomeM.value.trim() || salvando.value) return
  salvando.value = true
  try {
    utente.value = await api<Utente>(`/utenti/${sessione.id.value}`, { method: 'PATCH', body: { nome: nomeM.value.trim(), telefono: telM.value.trim() || null } })
    apertoModifica.value = false
    toast.ok('Profilo salvato')
  } catch (e) {
    toast.errore(messaggioErrore(e))
  } finally {
    salvando.value = false
  }
}

async function esci() {
  sessione.esci()
  await navigateTo('/benvenuto')
}

const COLORE: Record<string, string> = { basso: 'bg-macchia', medio: 'bg-ambra', alto: 'bg-brace', 'molto alto': 'bg-brace' }
</script>

<template>
  <div class="scorri flex flex-col gap-3 px-4 pb-4 pt-5">
    <header class="flex items-center gap-4">
      <span class="grid size-20 flex-none place-items-center rounded-full bg-inchiostro text-4xl font-extrabold text-white" aria-hidden="true">{{ iniziale(utente?.nome) }}</span>
      <div class="min-w-0 flex-1">
        <h1 class="titolo truncate text-[1.9rem]">{{ utente?.nome ?? '…' }}</h1>
        <p v-if="utente?.comune" class="tenue text-lg capitalize">{{ utente.comune.toLowerCase() }}</p>
      </div>
    </header>

    <div class="grid grid-cols-2 gap-3">
      <div class="scheda flex min-h-[9.5rem] flex-col justify-between gap-1.5">
        <span class="tenue">Telefono</span>
        <span class="whitespace-nowrap text-[1.05rem] font-extrabold leading-tight">{{ utente?.telefono ?? 'Non indicato' }}</span>
        <button type="button" class="pulsante pulsante-piccolo" @click="apriModifica">Modifica</button>
      </div>
      <div class="scheda flex min-h-[9.5rem] flex-col justify-between gap-1.5">
        <span class="tenue">Segnalazioni fatte</span>
        <span class="cifre text-[3.5rem] font-extrabold leading-none">{{ utente?.n_segnalazioni ?? 0 }}</span>
        <span class="tenue text-sm">{{ utente?.n_con_media ?? 0 }} con foto o video</span>
      </div>
    </div>

    <section class="scheda flex flex-col gap-2.5">
      <div class="flex items-center gap-2">
        <h2 class="sottotitolo flex-1">Luoghi che controllo</h2>
        <span v-if="luoghi.length" class="etichetta" :class="avvisi.lista.value.length ? 'e-brace' : 'e-macchia'">{{ avvisi.lista.value.length ? plurale(avvisi.lista.value.length, 'avviso', 'avvisi') : 'Avvisi attivi' }}</span>
      </div>
      <div v-if="luoghi.length" class="h-28 overflow-hidden rounded-2xl border-[1.5px] border-linea"><MappaBase :centro="[8.9, 39.45]" :zoom="9" :interattiva="false" @pronta="pronta" /></div>
      <ul v-if="luoghi.length" class="flex flex-col">
        <li v-for="l in luoghi" :key="l.id" class="flex min-h-12 items-center gap-3">
          <span class="size-3 flex-none rounded-full" :class="COLORE[l.stato.livello]" :aria-label="LIVELLI[l.stato.livello].nome" />
          <span class="flex-1 text-lg font-extrabold">{{ l.nome }}</span>
          <span class="tenue truncate text-base">{{ l.indirizzo ?? TIPI_LOCALITA[l.tipo] }}</span>
        </li>
      </ul>
      <p v-else class="tenue text-lg">Non hai ancora salvato nessun luogo.</p>
      <NuxtLink to="/localita" class="pulsante w-full">{{ luoghi.length ? 'Gestisci i luoghi' : 'Aggiungi casa' }}</NuxtLink>
    </section>

    <section class="elenco">
      <div class="riga !min-h-[4.5rem]">
        <Bell class="size-6 flex-none" aria-hidden="true" />
        <span class="flex-1"><span class="block text-lg font-extrabold leading-tight">Notifiche</span>
          <span class="tenue block text-sm">{{ avvisi.permesso.value === 'granted' ? 'Attive' : avvisi.permesso.value === 'denied' ? 'Bloccate nelle impostazioni del browser' : avvisi.permesso.value === 'non-supportato' ? 'Gli avvisi compaiono dentro l’app' : 'Non ancora consentite' }}</span></span>
        <button v-if="avvisi.permesso.value === 'default'" type="button" class="pulsante pulsante-piccolo" @click="avvisi.richiediPermesso()">Consenti</button>
      </div>
    </section>

    <button type="button" class="pulsante pulsante-fantasma mx-auto" @click="esci"><LogOut aria-hidden="true" />Cambia profilo</button>

    <!-- crediti: tolti dalla mappa, stanno qui -->
    <section class="tenue mt-1 border-t-[1.5px] border-linea pt-3 text-sm leading-relaxed" aria-labelledby="crediti">
      <h2 id="crediti" class="mb-1 text-sm font-extrabold text-inchiostro">Crediti</h2>
      <p>Mappa: © <a class="underline" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors, tile <a class="underline" href="https://protomaps.com" target="_blank" rel="noopener">Protomaps</a>.</p>
      <p>Immagini satellitari: Esri, Maxar, Earthstar Geographics e la comunità GIS.</p>
      <p>Carattere: Atkinson Hyperlegible Next, Braille Institute (licenza OFL). Icone: Lucide.</p>
    </section>

    <Foglio v-model="apertoModifica" titolo="Modifica il profilo">
      <h2 class="titolo mb-4 text-2xl">Il tuo profilo</h2>
      <form class="flex flex-col gap-3" @submit.prevent="salvaProfilo">
        <label class="etichetta-campo" for="m-nome">Nome</label>
        <div class="campo"><input id="m-nome" v-model="nomeM" maxlength="60" required></div>
        <label class="etichetta-campo" for="m-tel">Telefono</label>
        <div class="campo"><input id="m-tel" v-model="telM" type="tel" inputmode="tel" maxlength="24"></div>
        <div class="mt-2 flex gap-3">
          <button type="button" class="pulsante flex-1" @click="apertoModifica = false">Annulla</button>
          <button type="submit" class="pulsante pulsante-scuro flex-1" :disabled="salvando || !nomeM.trim()">Salva</button>
        </div>
      </form>
    </Foglio>
  </div>
</template>
