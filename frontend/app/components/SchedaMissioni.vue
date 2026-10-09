<script setup lang="ts">
import { Check, Droplets, Leaf, Trash2, Compass, HelpCircle, Star, X, Loader2, CircleCheck, CircleX, Flame } from '@lucide/vue'

const props = defineProps<{ utente: Utente }>()
const emit = defineEmits<{ esito: [EsitoMissione]; posizione: [Missione] }>()
const { chiama } = useApi()

const missioni = ref<Missione[]>([])
const errore = ref('')
const caricamento = ref(true)
const erroreElenco = ref('')
const attiva = ref<Missione | null>(null)
const inCorso = ref(false)

// quiz
const domande = ref<DomandaQuiz[]>([])
const risposte = ref<number[]>([])
const passo = ref(0)
const risultato = ref<EsitoMissione | null>(null)

// esplora
const righe = ref<{ anno: number; incendi: number; ettari: number }[]>([])
const caricandoStat = ref(false)

const ICONE: Record<string, any> = { quiz_rischio: HelpCircle, punto_acqua: Droplets, sterpaglie: Leaf, rifiuti_strada: Trash2, esplora_comune: Compass }

async function carica() {
  erroreElenco.value = ''
  if (!missioni.value.length) caricamento.value = true
  try { missioni.value = await chiama<Missione[]>(`/missioni?utente_id=${props.utente.id}`) }
  catch (e) { erroreElenco.value = messaggioErrore(e, 'caricare le missioni') }
  caricamento.value = false
}
onMounted(carica)
defineExpose({ carica })

async function apri(m: Missione) {
  if (!m.disponibile) return
  errore.value = ''
  if (m.tipo === 'posizione') { emit('posizione', m); return }
  attiva.value = m; risultato.value = null
  if (m.tipo === 'quiz') {
    try { domande.value = await chiama<DomandaQuiz[]>('/quiz/oggi'); risposte.value = []; passo.value = 0 }
    catch (e) { errore.value = messaggioErrore(e, 'aprire il quiz'); attiva.value = null }
  } else await statistiche()
}

function chiudi() { attiva.value = null; risultato.value = null; carica() }

async function completa(m: Missione, extra: Record<string, string> = {}) {
  inCorso.value = true; errore.value = ''
  const f = new FormData()
  f.append('utente_id', String(props.utente.id))
  for (const [k, v] of Object.entries(extra)) f.append(k, v)
  try {
    const r = await chiama<EsitoMissione>(`/missioni/${m.id}/completa`, { method: 'POST', body: f })
    emit('esito', r)
    return r
  } catch (e: any) {
    errore.value = String(e.message).startsWith('409') ? 'Missione già completata (limite raggiunto).' : messaggioErrore(e, 'completare la missione')
  } finally { inCorso.value = false }
}

function rispondi(i: number) {
  risposte.value = [...risposte.value, i]
  if (risposte.value.length < domande.value.length) passo.value++
}

async function consegna() {
  const r = await completa(attiva.value!, { risposte: JSON.stringify(risposte.value) })
  if (r) risultato.value = r
}

async function statistiche() {
  caricandoStat.value = true; righe.value = []
  try {
    const g = await chiama<{ per_anno: { anno: number; incendi: number; ettari: number }[] }>(`/storico/statistiche?comune=${encodeURIComponent(props.utente.comune)}&anno_da=2015`)
    righe.value = [...g.per_anno].sort((a, b) => b.anno - a.anno)
  } catch (e) { errore.value = messaggioErrore(e, 'caricare le statistiche') }
  caricandoStat.value = false
}
const giuste = computed(() => risultato.value?.esiti?.filter((e) => e.giusta).length ?? 0)
const totEttari = computed(() => righe.value.reduce((a, r) => a + r.ettari, 0))
const totIncendi = computed(() => righe.value.reduce((a, r) => a + r.incendi, 0))
const maxEttari = computed(() => Math.max(1, ...righe.value.map((r) => r.ettari)))

async function completaEsplora() {
  const r = await completa(attiva.value!)
  if (r) chiudi()
}
</script>

<template>
  <div class="p-3">
    <p v-if="errore" class="mb-3 rounded-m border border-brace/40 bg-brace/10 p-3 text-sm text-brace" role="alert">{{ errore }}</p>

    <!-- elenco -->
    <template v-if="!attiva">
      <p class="etichetta">Oggi</p>
      <h2 class="mt-0.5 mb-3 text-lg font-semibold tracking-tight">Missioni di prevenzione</h2>
      <StatoErrore v-if="erroreElenco" :messaggio="erroreElenco" @riprova="carica" />
      <ul v-else-if="caricamento" class="space-y-2" aria-busy="true" aria-label="Caricamento delle missioni">
        <li v-for="k in 4" :key="k" class="vetro flex items-center gap-3 p-3">
          <span class="scheletro size-9 shrink-0" />
          <span class="flex-1 space-y-2"><span class="scheletro block h-3.5 w-36" /><span class="scheletro block h-2.5 w-48 max-w-full" /></span>
          <span class="scheletro h-6 w-11 !rounded-full" />
        </li>
      </ul>
      <p v-else-if="!missioni.length" class="vetro p-5 text-center text-sm text-testo-2">Nessuna missione per oggi. Torna domani.</p>
      <ul v-else class="space-y-2">
        <li v-for="m in missioni" :key="m.id">
          <button type="button" class="vetro flex w-full items-center gap-3 p-3 text-left transition-colors" :class="m.disponibile ? 'hover:bg-vetro-forte active:bg-vetro-forte' : 'opacity-75'" :disabled="!m.disponibile" @click="apri(m)">
            <span class="flex size-9 shrink-0 items-center justify-center rounded-s ring-1" :class="m.disponibile ? 'bg-brace/12 text-brace ring-brace/25' : 'bg-macchia/12 text-macchia ring-macchia/25'">
              <Check v-if="!m.disponibile" class="size-4" aria-hidden="true" /><component :is="ICONE[m.codice] ?? Compass" v-else class="size-4" aria-hidden="true" />
            </span>
            <span class="min-w-0 flex-1 leading-tight">
              <span class="block text-[.9rem] font-semibold">{{ m.titolo }}</span>
              <span class="mt-0.5 block text-[.78rem]" :class="m.disponibile ? 'text-testo-2' : 'text-macchia'">{{ m.disponibile ? m.descrizione : (m.motivo ?? 'Completata') }}</span>
            </span>
            <span class="cifre flex shrink-0 items-center gap-1 text-[.8rem] font-semibold text-ambra"><Star class="size-3 fill-current" aria-hidden="true" />{{ m.punti }}</span>
          </button>
        </li>
      </ul>
    </template>

    <!-- quiz -->
    <section v-else-if="attiva.tipo === 'quiz'" class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="etichetta">Quiz · +{{ attiva.punti }} punti</p>
          <h2 class="mt-0.5 text-base font-semibold">{{ attiva.titolo }}</h2>
        </div>
        <button type="button" aria-label="Chiudi il quiz" class="secondario tocco flex size-9 shrink-0 items-center justify-center" @click="chiudi"><X class="size-[18px]" /></button>
      </div>
      <template v-if="!risultato">
        <div v-if="domande.length" class="flex gap-1.5" aria-hidden="true">
          <span v-for="(_, k) in domande" :key="k" class="h-1 flex-1 rounded-full transition-colors duration-300" :class="k < risposte.length ? 'bg-brace' : k === passo ? 'bg-testo-3' : 'bg-bordo-luce'" />
        </div>
        <template v-if="domande.length && risposte.length < domande.length">
          <p class="cifre text-[.78rem] font-semibold text-testo-2">Domanda {{ passo + 1 }} di {{ domande.length }}</p>
          <p class="text-[1.05rem] font-semibold leading-snug">{{ domande[passo]!.domanda }}</p>
          <div class="space-y-2">
            <button v-for="(o, i) in domande[passo]!.opzioni" :key="i" type="button" class="vetro flex w-full items-center gap-3 p-3 text-left transition-colors hover:bg-vetro-forte active:bg-vetro-forte" @click="rispondi(i)">
              <span class="flex size-6 shrink-0 items-center justify-center rounded-s bg-vetro-forte text-[.72rem] font-semibold text-testo-2 ring-1 ring-bordo-luce">{{ String.fromCharCode(65 + i) }}</span>
              <span class="text-[.92rem]">{{ o }}</span>
            </button>
          </div>
        </template>
        <template v-else-if="domande.length">
          <div class="vetro flex flex-col items-center gap-2 p-5 text-center">
            <CircleCheck class="size-7 text-macchia" aria-hidden="true" />
            <p class="font-semibold">Hai risposto a tutte le domande</p>
            <p class="text-sm text-testo-2">Consegna per vedere il risultato e le spiegazioni.</p>
          </div>
          <button class="primario flex h-12 w-full items-center justify-center gap-2 text-[.95rem]" :disabled="inCorso" @click="consegna"><Loader2 v-if="inCorso" class="size-5 animate-spin" />{{ inCorso ? 'Invio…' : 'Consegna' }}</button>
        </template>
        <p v-else class="flex items-center justify-center gap-2 p-6 text-sm text-testo-2"><Loader2 class="size-4 animate-spin" /> Caricamento…</p>
      </template>
      <template v-else>
        <div class="vetro flex items-center gap-4 p-4">
          <p class="cifre text-4xl font-semibold tracking-tight">{{ giuste }}<span class="text-2xl text-testo-3">/{{ risultato.esiti?.length }}</span></p>
          <div class="leading-tight">
            <p class="font-semibold">{{ giuste === risultato.esiti?.length ? 'Tutte giuste!' : 'Risposte giuste' }}</p>
            <p class="cifre mt-1 inline-flex items-center gap-1 text-[.8rem] font-semibold text-ambra"><Star class="size-3.5 fill-current" aria-hidden="true" /> +{{ risultato.punti_ottenuti }} punti</p>
          </div>
        </div>
        <div v-for="e in risultato.esiti" :key="e.indice" class="vetro space-y-1.5 p-3 text-[.86rem]">
          <p class="flex items-start gap-2 font-semibold">
            <CircleCheck v-if="e.giusta" class="mt-0.5 size-4 shrink-0 text-macchia" aria-label="Giusta" />
            <CircleX v-else class="mt-0.5 size-4 shrink-0 text-brace" aria-label="Sbagliata" />
            {{ domande[e.indice]?.domanda }}
          </p>
          <p class="pl-6" :class="e.giusta ? 'text-macchia' : 'text-brace'">{{ e.giusta ? 'Giusta' : 'Tua' }}: {{ domande[e.indice]?.opzioni[risposte[e.indice]!] }}</p>
          <p v-if="!e.giusta" class="pl-6 text-macchia">Corretta: {{ domande[e.indice]?.opzioni[e.corretta] }}</p>
          <p class="pl-6 text-testo-2">{{ e.spiegazione }}</p>
        </div>
        <button class="secondario h-10 w-full text-sm" @click="chiudi">Fatto</button>
      </template>
    </section>

    <!-- esplora -->
    <section v-else class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="etichetta">Esplora · +{{ attiva.punti }} punti</p>
          <h2 class="mt-0.5 text-base font-semibold">Incendi a {{ nomeComune(utente.comune) }}</h2>
        </div>
        <button type="button" aria-label="Chiudi" class="secondario tocco flex size-9 shrink-0 items-center justify-center" @click="chiudi"><X class="size-[18px]" /></button>
      </div>
      <p v-if="caricandoStat" class="flex items-center justify-center gap-2 p-6 text-sm text-testo-2"><Loader2 class="size-4 animate-spin" /> Caricamento…</p>
      <p v-else-if="!righe.length" class="vetro p-4 text-sm text-testo-2">Nessun incendio registrato in archivio per il tuo comune.</p>
      <template v-else>
        <div class="grid grid-cols-2 gap-2">
          <div class="vetro p-3"><p class="etichetta">Incendi dal 2015</p><p class="cifre mt-1 text-2xl font-semibold">{{ totIncendi }}</p></div>
          <div class="vetro p-3"><p class="etichetta">Ettari bruciati</p><p class="cifre mt-1 text-2xl font-semibold">{{ totEttari.toFixed(0) }}<span class="text-base text-testo-3"> ha</span></p></div>
        </div>
        <ul class="vetro space-y-2.5 p-3">
          <li v-for="r in righe" :key="r.anno" class="text-[.82rem]">
            <div class="flex items-baseline justify-between"><span class="cifre font-semibold">{{ r.anno }}</span><span class="cifre text-testo-2">{{ r.incendi }} incendi · {{ r.ettari.toFixed(1) }} ha</span></div>
            <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-bordo-luce"><div class="h-full rounded-full bg-gradient-to-r from-ambra to-brace" :style="{ width: Math.max(2, r.ettari / maxEttari * 100) + '%' }" /></div>
          </li>
        </ul>
        <p class="text-[.75rem] text-testo-3">Dati storici regionali (CFVA), per anno.</p>
      </template>
      <button class="primario flex h-12 w-full items-center justify-center gap-2 text-[.95rem]" :disabled="inCorso || caricandoStat" @click="completaEsplora"><Loader2 v-if="inCorso" class="size-5 animate-spin" />{{ inCorso ? 'Invio…' : `Completa · +${attiva.punti} punti` }}</button>
    </section>
  </div>
</template>
