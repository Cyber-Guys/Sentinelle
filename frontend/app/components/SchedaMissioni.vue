<script setup lang="ts">
import { Check, Droplets, Leaf, Trash2, Compass, HelpCircle, Star, ChevronRight } from '@lucide/vue'

const props = defineProps<{ utente: Utente; centro: [number, number] }>()
const emit = defineEmits<{ esito: [EsitoMissione]; posizione: [Missione] }>()
const { chiama } = useApi()

const missioni = ref<Missione[]>([])
const errore = ref('')
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
  try { missioni.value = await chiama<Missione[]>(`/missioni?utente_id=${props.utente.id}`) }
  catch (e: any) { errore.value = 'Missioni non disponibili: ' + e.message }
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
    catch (e: any) { errore.value = 'Quiz non disponibile: ' + e.message; attiva.value = null }
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
    errore.value = String(e.message).startsWith('409') ? 'Missione gia completata (limite raggiunto).' : 'Operazione non riuscita: ' + e.message
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
  const [lon, lat] = props.centro
  try {
    const g = await chiama<any>(`/storico/incendi?bbox=${lon - 0.12},${lat - 0.1},${lon + 0.12},${lat + 0.1}&anno_da=2015&anno_a=2025`)
    const per: Record<number, { anno: number; incendi: number; ettari: number }> = {}
    for (const f of g.features) {
      const p = f.properties
      if (p.comune !== props.utente.comune) continue
      const r = (per[p.anno] ??= { anno: p.anno, incendi: 0, ettari: 0 })
      r.incendi++; r.ettari += Number(p.ettari_totali ?? 0)
    }
    righe.value = Object.values(per).sort((a, b) => b.anno - a.anno)
  } catch (e: any) { errore.value = 'Statistiche non disponibili' }
  caricandoStat.value = false
}
const maxEttari = computed(() => Math.max(1, ...righe.value.map((r) => r.ettari)))

async function completaEsplora() {
  const r = await completa(attiva.value!)
  if (r) chiudi()
}
</script>

<template>
  <div class="space-y-3 p-4">
    <p v-if="errore" class="text-sm text-alta">{{ errore }}</p>

    <!-- elenco -->
    <template v-if="!attiva">
      <h2 class="text-lg font-bold">Missioni di prevenzione</h2>
      <button v-for="m in missioni" :key="m.id" type="button" class="flex w-full items-center gap-3 rounded-xl border p-3 text-left" :class="m.disponibile ? 'border-bordo bg-carta active:bg-bosco-chiaro' : 'border-bordo bg-fondo opacity-70'" :disabled="!m.disponibile" @click="apri(m)">
        <span class="flex size-11 shrink-0 items-center justify-center rounded-full" :class="m.disponibile ? 'bg-orange-50 text-fuoco' : 'bg-bosco-chiaro text-bosco'">
          <Check v-if="!m.disponibile" class="size-6" /><component :is="ICONE[m.codice] ?? Compass" v-else class="size-6" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block font-semibold">{{ m.titolo }}</span>
          <span class="block text-xs text-testo-2">{{ m.disponibile ? m.descrizione : (m.motivo ?? 'Completata') }}</span>
        </span>
        <span class="flex shrink-0 items-center gap-0.5 text-sm font-bold text-bosco"><Star class="size-3.5" />{{ m.punti }}</span>
        <ChevronRight v-if="m.disponibile" class="size-4 shrink-0 text-testo-2" />
      </button>
    </template>

    <!-- quiz -->
    <section v-else-if="attiva.tipo === 'quiz'" class="space-y-3">
      <div class="flex items-center justify-between"><h2 class="text-lg font-bold">{{ attiva.titolo }}</h2><button class="text-sm text-testo-2" @click="chiudi">Chiudi</button></div>
      <template v-if="!risultato">
        <template v-if="domande.length && risposte.length < domande.length">
          <p class="text-xs font-semibold text-testo-2">Domanda {{ passo + 1 }} di {{ domande.length }}</p>
          <p class="text-lg font-bold">{{ domande[passo]!.domanda }}</p>
          <button v-for="(o, i) in domande[passo]!.opzioni" :key="i" type="button" class="w-full rounded-xl border border-bordo bg-carta p-3 text-left active:bg-bosco-chiaro" @click="rispondi(i)">{{ o }}</button>
        </template>
        <template v-else-if="domande.length">
          <p class="font-semibold">Hai risposto a tutte le domande.</p>
          <button class="primario w-full py-4 text-lg disabled:opacity-50" :disabled="inCorso" @click="consegna">{{ inCorso ? 'Invio…' : 'Consegna' }}</button>
        </template>
      </template>
      <template v-else>
        <p class="rounded-xl bg-bosco-chiaro p-3 text-center font-bold text-bosco">{{ risultato.esiti?.filter((e) => e.giusta).length }} su {{ risultato.esiti?.length }} giuste: +{{ risultato.punti_ottenuti }} punti</p>
        <div v-for="e in risultato.esiti" :key="e.indice" class="space-y-1 rounded-xl border p-3 text-sm" :class="e.giusta ? 'border-bassa' : 'border-alta'">
          <p class="font-bold">{{ domande[e.indice]?.domanda }}</p>
          <p :class="e.giusta ? 'text-bassa' : 'text-alta'">Tu: {{ domande[e.indice]?.opzioni[risposte[e.indice]!] }}</p>
          <p v-if="!e.giusta" class="text-bassa">Corretta: {{ domande[e.indice]?.opzioni[e.corretta] }}</p>
          <p class="text-testo-2">{{ e.spiegazione }}</p>
        </div>
        <button class="secondario w-full py-3" @click="chiudi">Fatto</button>
      </template>
    </section>

    <!-- esplora -->
    <section v-else class="space-y-3">
      <div class="flex items-center justify-between"><h2 class="text-lg font-bold">Incendi a <span class="capitalize">{{ utente.comune.toLowerCase() }}</span></h2><button class="text-sm text-testo-2" @click="chiudi">Chiudi</button></div>
      <p class="text-sm text-testo-2">Incendi ed ettari bruciati per anno, dal 2015 (dati storici regionali).</p>
      <p v-if="caricandoStat" class="text-sm text-testo-2">Caricamento…</p>
      <p v-else-if="!righe.length" class="text-sm text-testo-2">Nessun incendio registrato in archivio per il tuo comune.</p>
      <ul class="space-y-1.5">
        <li v-for="r in righe" :key="r.anno" class="text-sm">
          <div class="flex justify-between"><span class="font-semibold">{{ r.anno }}</span><span class="text-testo-2">{{ r.incendi }} incendi · {{ r.ettari.toFixed(1) }} ha</span></div>
          <div class="mt-0.5 h-2 overflow-hidden rounded-full bg-bosco-chiaro"><div class="h-full rounded-full bg-fuoco" :style="{ width: (r.ettari / maxEttari * 100) + '%' }" /></div>
        </li>
      </ul>
      <button class="primario w-full py-4 text-lg disabled:opacity-50" :disabled="inCorso || caricandoStat" @click="completaEsplora">{{ inCorso ? 'Invio…' : `Completa (+${attiva.punti} punti)` }}</button>
    </section>
  </div>
</template>
