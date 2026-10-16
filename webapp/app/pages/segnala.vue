<script setup lang="ts">
// Segnala: foto o video, che cosa si vede, invio. Tre tocchi: foto, tipo, "Invia segnalazione".
import { Camera, Check, ChevronLeft, LoaderCircle, MapPin, Mic, Pencil, Send, Video, X } from '@lucide/vue'

definePageMeta({ layout: 'pieno' })

const api = useApi()
const { id } = useSessione()
const { pos } = usePosizione()
const { dir } = useBussola()
const bozza = useBozza()
const toast = useToast()

const invio = ref(false)
const inviata = ref<Segnalazione | null>(null)
const scegliPunto = ref(false)
const puntoTemp = ref<{ lat: number; lon: number } | null>(null)
const luogo = ref('')
const luogoInviato = ref('') // il luogo del riepilogo: non cambia se la posizione si aggiorna dopo l'invio

// anteprime dei file scelti (si liberano quando cambiano o si esce)
const urlFoto = ref<string>()
const urlVideo = ref<string>()
watch(bozza.foto, (f) => { if (urlFoto.value) URL.revokeObjectURL(urlFoto.value); urlFoto.value = f ? URL.createObjectURL(f) : undefined }, { immediate: true })
watch(bozza.video, (f) => { if (urlVideo.value) URL.revokeObjectURL(urlVideo.value); urlVideo.value = f ? URL.createObjectURL(f) : undefined }, { immediate: true })
onBeforeUnmount(() => { if (urlFoto.value) URL.revokeObjectURL(urlFoto.value); if (urlVideo.value) URL.revokeObjectURL(urlVideo.value) })

const dove = computed(() => bozza.punto.value ?? pos.value)
const megabyte = (f: File) => `${(f.size / 1e6).toFixed(1).replace('.', ',')} MB`

function prendi(e: Event, dove: 'foto' | 'video') {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  input.value = ''
  if (!f) return
  if (dove === 'foto') bozza.foto.value = f
  else bozza.video.value = f
}

// dettatura a voce, dove il browser la offre (Chrome)
const Riconoscimento = import.meta.client ? (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition : null
function parla() {
  if (!Riconoscimento) { toast.errore('La dettatura a voce non è disponibile su questo browser.'); return }
  const r = new Riconoscimento()
  r.lang = 'it-IT'
  r.onresult = (e: any) => { bozza.nota.value = `${bozza.nota.value} ${e.results[0][0].transcript}`.trim() }
  r.onerror = () => toast.errore('Non ho sentito bene. Riprova.')
  r.start()
}

async function cercaLuogo() {
  try {
    const l = await api<{ comune: string | null; indirizzo: string | null }>('/luogo', { query: { lat: dove.value.lat, lon: dove.value.lon } })
    luogo.value = [l.indirizzo, l.comune].filter(Boolean).join(', ')
  } catch { luogo.value = '' }
}
watch(dove, cercaLuogo, { immediate: true })

function confermaPunto() {
  if (puntoTemp.value) bozza.punto.value = puntoTemp.value
  scegliPunto.value = false
}

async function invia() {
  if (!bozza.tipo.value || invio.value) return
  invio.value = true
  try {
    const f = new FormData()
    f.append('utente_id', String(id.value))
    f.append('tipo', bozza.tipo.value)
    f.append('lat', String(dove.value.lat))
    f.append('lon', String(dove.value.lon))
    if (dir.value !== null) f.append('direzione', String(Math.round(dir.value)))
    if (bozza.nota.value.trim()) f.append('nota', bozza.nota.value.trim())
    if (bozza.foto.value) f.append('foto', await ridimensiona(bozza.foto.value))
    if (bozza.video.value) f.append('video', bozza.video.value)
    inviata.value = await api<Segnalazione>('/segnalazioni', { method: 'POST', body: f })
    luogoInviato.value = luogo.value
    bozza.azzera()
  } catch (e) {
    toast.errore(messaggioErrore(e))
  } finally {
    invio.value = false
  }
}

const priorita = (n: number) => (n >= 60 ? 'alta' : n >= 30 ? 'media' : 'bassa')
</script>

<template>
  <!-- dopo l'invio: il riepilogo in alto occupa lo spazio, i due bottoni stanno sempre in fondo -->
  <template v-if="inviata">
    <div class="scorri flex flex-col items-center gap-4 px-5 pb-4 pt-10 text-center">
      <span class="grid size-24 place-items-center rounded-full bg-macchia text-white shadow-sollevato"><Check class="size-14" stroke-width="3" aria-hidden="true" /></span>
      <h1 class="titolo text-[1.9rem]">Segnalazione inviata</h1>
      <p class="tenue max-w-[21rem] text-lg leading-snug">Grazie per quello che hai fatto. Gli operatori verranno informati e si muoveranno il prima possibile.</p>

      <div class="scheda mt-2 w-full !p-5 text-left">
        <div class="flex items-center gap-4">
          <span class="tile-tipo !size-[4.5rem] !rounded-2xl [&>svg]:!size-9" :class="`t-${inviata.tipo}`"><IconaTipo :tipo="inviata.tipo" aria-hidden="true" /></span>
          <div class="min-w-0 flex-1">
            <p class="titolo text-[1.7rem] leading-tight">{{ TIPI[inviata.tipo].nome }}</p>
            <p class="tenue text-lg font-semibold">Segnalato ora</p>
          </div>
        </div>
        <div v-if="luogoInviato" class="mt-4 border-t-[1.5px] border-linea pt-3">
          <p class="tenue text-sm font-bold">Dove</p>
          <p class="flex items-start gap-2 text-xl font-semibold leading-snug"><MapPin class="mt-0.5 size-5 flex-none" aria-hidden="true" />{{ luogoInviato }}</p>
        </div>
        <div v-if="inviata.nota" class="mt-3 border-t-[1.5px] border-linea pt-3">
          <p class="tenue text-sm font-bold">La tua nota</p>
          <p class="text-xl leading-snug">{{ inviata.nota }}</p>
        </div>
      </div>
    </div>

    <div class="flex flex-none flex-col gap-3 border-t-[1.5px] border-linea bg-carta px-4 pb-4 pt-3">
      <NuxtLink to="/" class="gigante !min-h-[4.5rem] !text-xl">Torna alla mappa</NuxtLink>
      <NuxtLink to="/storico" class="pulsante w-full">Vedi nello storico</NuxtLink>
    </div>
  </template>

  <!-- modulo -->
  <template v-else>
    <div class="scorri flex flex-col gap-3 px-4 pb-3 pt-3">
      <NuxtLink to="/" class="indietro self-start"><ChevronLeft class="size-6" aria-hidden="true" />Indietro</NuxtLink>

      <!-- anteprima -->
      <div class="relative h-60 flex-none overflow-hidden rounded-3xl bg-vuoto">
        <img v-if="urlFoto" :src="urlFoto" alt="La foto che hai scattato" class="size-full object-cover">
        <video v-else-if="urlVideo" :src="urlVideo" class="size-full object-cover" muted playsinline preload="metadata" />
        <label v-else class="tenue flex size-full cursor-pointer flex-col items-center justify-center gap-2 text-lg font-bold">
          <Camera class="size-12" aria-hidden="true" />
          Aggiungi una foto
          <input type="file" accept="image/*" capture="environment" class="sr-only" @change="prendi($event, 'foto')">
        </label>
        <template v-if="urlFoto || urlVideo">
          <label class="pulsante pulsante-piccolo absolute right-3 top-3 cursor-pointer">Cambia
            <input type="file" accept="image/*" capture="environment" class="sr-only" @change="prendi($event, 'foto')">
          </label>
          <span class="absolute inset-x-0 bottom-3 mx-auto w-fit rounded-full bg-inchiostro/80 px-4 py-1.5 font-bold text-white">La tua foto</span>
        </template>
      </div>

      <h1 class="sottotitolo text-center text-[1.4rem]">Cosa hai fotografato?</h1>
      <div class="grid grid-cols-3 gap-2.5" role="group" aria-label="Tipo di segnalazione">
        <TesseraTipo v-for="t in (['fuoco', 'fumo', 'area_a_rischio'] as const)" :key="t" :tipo="t" :attiva="bozza.tipo.value === t" @click="bozza.tipo.value = t" />
      </div>

      <!-- ALLEGATI (video, foto aggiuntive): nascosti per ora, il codice resta pronto (prendi() e il video nello script).
            <div class="scheda flex flex-col gap-2.5">
        <div class="flex items-baseline justify-between"><span class="text-lg font-extrabold">Allega</span><span class="tenue text-sm">Facoltativo</span></div>
        <div class="grid grid-cols-3 gap-2.5">
          <div class="relative">
            <label class="pulsante !flex-col !gap-1 !rounded-2xl !py-2 h-20 w-full cursor-pointer" :class="bozza.foto.value ? '!border-macchia !bg-macchia-fondo' : ''">
              <Camera aria-hidden="true" /><span>Foto</span>
              <input type="file" accept="image/*" capture="environment" class="sr-only" @change="prendi($event, 'foto')">
            </label>
            <button v-if="bozza.foto.value" type="button" class="absolute -right-1.5 -top-1.5 grid size-8 place-items-center rounded-full border-2 border-white bg-inchiostro text-white" :aria-label="`Togli la foto (${megabyte(bozza.foto.value)})`" @click="bozza.foto.value = null"><X class="size-4" aria-hidden="true" /></button>
          </div>
          <div class="relative">
            <label class="pulsante !flex-col !gap-1 !rounded-2xl !py-2 h-20 w-full cursor-pointer" :class="bozza.video.value ? '!border-macchia !bg-macchia-fondo' : ''">
              <Video aria-hidden="true" /><span>Video</span>
              <input type="file" accept="video/*" capture="environment" class="sr-only" @change="prendi($event, 'video')">
            </label>
            <button v-if="bozza.video.value" type="button" class="absolute -right-1.5 -top-1.5 grid size-8 place-items-center rounded-full border-2 border-white bg-inchiostro text-white" :aria-label="`Togli il video (${megabyte(bozza.video.value)})`" @click="bozza.video.value = null"><X class="size-4" aria-hidden="true" /></button>
          </div>
          <button type="button" class="pulsante !flex-col !gap-1 !rounded-2xl !py-2 h-20" :class="bozza.nota.value ? '!border-macchia !bg-macchia-fondo' : ''" :aria-expanded="notaAperta" @click="notaAperta = !notaAperta">
            <Pencil aria-hidden="true" /><span>Nota</span>
          </button>
        </div>
        <div v-if="notaAperta" class="campo !items-start py-2">
          <label for="nota" class="sr-only">Nota</label>
          <textarea id="nota" v-model="bozza.nota.value" rows="3" maxlength="500" placeholder="Per esempio: dietro la chiesa, vicino al campo" class="resize-none" />
          <button v-if="Riconoscimento" type="button" class="tondo !size-11 !shadow-none" aria-label="Detta a voce" @click="parla"><Mic aria-hidden="true" /></button>
        </div>
      </div>

      -->

      <!-- nota facoltativa, anche a voce -->
      <div class="flex flex-col gap-1.5">
        <label for="nota" class="etichetta-campo">Nota <span class="tenue font-normal">(facoltativa)</span></label>
        <div class="campo !items-start py-2">
          <textarea id="nota" v-model="bozza.nota.value" rows="3" maxlength="500" placeholder="Per esempio: dietro la chiesa, vicino al campo" class="resize-none" />
          <button type="button" class="tondo !size-11 !shadow-none" aria-label="Detta la nota a voce" @click="parla"><Mic aria-hidden="true" /></button>
        </div>
      </div>

      <!-- dove -->
      <div class="flex min-h-12 items-center gap-2.5">
        <MapPin class="size-6 flex-none" aria-hidden="true" />
        <p class="flex-1 text-base leading-tight">
          <span class="font-bold">{{ bozza.punto.value ? 'Punto scelto sulla mappa' : luogo || 'La tua posizione' }}</span>
          <span v-if="dir !== null && !bozza.punto.value" class="tenue block">Guardavi verso {{ puntoCardinale(dir) }}</span>
        </p>
        <button type="button" class="pulsante pulsante-piccolo" @click="puntoTemp = dove; scegliPunto = true">Cambia</button>
      </div>
    </div>

    <!-- invio sempre in fondo -->
    <div class="flex-none border-t-[1.5px] border-linea bg-carta px-4 pb-4 pt-3">
      <button type="button" class="gigante !min-h-[4.75rem] !text-[1.4rem]" :disabled="!bozza.tipo.value || invio" @click="invia">
        <LoaderCircle v-if="invio" class="gira" aria-hidden="true" />
        <Send v-else-if="bozza.tipo.value" aria-hidden="true" />
        {{ invio ? 'Invio in corso…' : bozza.tipo.value ? 'Invia segnalazione' : 'Scegli cosa hai visto' }}
      </button>
      <p class="tenue mt-2 text-center text-sm">In pericolo? Chiama il 112 o il 1515.</p>
    </div>

    <Foglio v-model="scegliPunto" titolo="Scegli il punto">
      <h2 class="titolo mb-3 text-2xl">Dov’è?</h2>
      <div class="h-72 overflow-hidden rounded-2xl"><MappaPunto :centro="dove" :icona="bozza.tipo.value ?? 'fuoco'" @muovi="puntoTemp = $event" /></div>
      <p class="tenue mt-2 text-base">Muovi la mappa: il segnaposto resta al centro.</p>
      <button type="button" class="gigante !min-h-[4.25rem] !text-xl mt-3" @click="confermaPunto">Usa questo punto</button>
    </Foglio>
  </template>
</template>
