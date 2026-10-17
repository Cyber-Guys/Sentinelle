<script setup lang="ts">
import { Flame, Cloud, Sparkles, ImageOff, Users, ThumbsUp, ThumbsDown, ShieldCheck, OctagonX, ChevronDown, Camera, MapPin, Quote, Inbox } from '@lucide/vue'
import { raggruppa, valutaFoto, dentro, fmtOre, distanzaKm, SOGLIA_PERTINENZA, type AreaCop, type FotoValutata } from '~/composables/useCop'
import { nomeComune, varPriorita, etichettaPriorita } from '~/composables/useApi'

type Segn = { id: number; tipo: string; lat: number; lon: number; foto_url: string | null; nota: string | null; priorita: number; comune: string | null; creata_il: string; conferme: number; smentite: number }
type Aff = { valore: number; livello: string; etichetta: string }
const props = defineProps<{ segnalazioni: Segn[]; affidabilita: Record<number, Aff>; area: AreaCop | null; ora: number }>()
const emit = defineEmits<{ certificato: [esito: { luogo: string; avvisati: number; centro: [number, number] }]; archiviato: [luogo: string] }>()
const selezionato = defineModel<number | null>('selezionato', { default: null })

const { chiama, urlFoto } = useApi()
const soloArea = ref(true)
const nell = (s: Segn) => !props.area || dentro([s.lon, s.lat], props.area.geometria)
const gruppi = computed(() => raggruppa(props.segnalazioni.filter((s) => !soloArea.value || nell(s))).map((g) => {
  const capo = g[0]!
  const foto = g.filter((s) => s.foto_url).map((s) => valutaFoto(urlFoto(s.foto_url)!, s.id)).sort((a, b) => b.pertinenza - a.pertinenza)
  const aff = props.affidabilita[capo.id]
  return {
    id: capo.id, capo, membri: g, foto, pertinenti: foto.filter((f) => f.pertinenza >= SOGLIA_PERTINENZA), scartate: foto.filter((f) => f.pertinenza < SOGLIA_PERTINENZA),
    conferme: g.reduce((s, x) => s + x.conferme, 0), smentite: g.reduce((s, x) => s + x.smentite, 0), aff,
    luogo: nomeComune(capo.comune) || 'Località sconosciuta', prima: g.reduce((m, x) => (x.creata_il < m ? x.creata_il : m), capo.creata_il),
    fuoco: g.some((x) => x.tipo === 'fuoco'), note: g.filter((x) => x.nota).map((x) => x.nota!),
  }
}))
const fuoriArea = computed(() => props.area ? raggruppa(props.segnalazioni.filter((s) => !nell(s))).length : 0)
const gruppo = computed(() => gruppi.value.find((g) => g.membri.some((m) => m.id === selezionato.value)) ?? gruppi.value[0] ?? null)
watch(gruppo, (g) => { if (g && !g.membri.some((m) => m.id === selezionato.value)) selezionato.value = g.id }, { immediate: true })

const fotoSel = ref<FotoValutata | null>(null)
const mostraScartate = ref(false)
watch(() => gruppo.value?.id, () => { fotoSel.value = gruppo.value?.pertinenti[0] ?? null; mostraScartate.value = false; avvisa.value = true }, { immediate: true })

// segnali di validazione: quanto peso ha il gruppo prima che l'operatore guardi le foto
const segnali = computed(() => {
  const g = gruppo.value
  if (!g) return []
  return [
    { icona: Users, titolo: 'Segnalazioni congiunte', valore: String(g.membri.length), nota: g.membri.length > 1 ? 'entro 2,5 km, persone diverse' : 'una sola persona', forte: g.membri.length > 1 },
    { icona: ThumbsUp, titolo: 'Conferme dai vicini', valore: String(g.conferme), nota: 'risposte a "C\'è un incendio vicino a te?"', forte: g.conferme >= 3 },
    { icona: ThumbsDown, titolo: "Risposte \"non c'è\"", valore: String(g.smentite), nota: g.smentite ? 'da valutare con le foto' : 'nessuna smentita', forte: false, debole: g.smentite > g.conferme },
    { icona: Camera, titolo: 'Foto pertinenti', valore: `${g.pertinenti.length}/${g.foto.length}`, nota: 'selezione AI simulata', forte: g.pertinenti.length > 0 },
  ]
})

const avvisa = ref(true)
const inCorso = ref<'certifica' | 'archivia' | null>(null)
const errore = ref('')
async function certifica() {
  const g = gruppo.value
  if (!g || inCorso.value) return
  inCorso.value = 'certifica'; errore.value = ''
  try {
    const r = await chiama<{ avvisati: number }>(avvisa.value ? `/cop/segnalazioni/${g.id}/certifica` : `/segnalazioni/${g.id}/conferma`, { method: 'POST' })
    await Promise.all(g.membri.slice(1).map((m) => chiama(`/segnalazioni/${m.id}/conferma`, { method: 'POST' })))
    emit('certificato', { luogo: g.luogo, avvisati: avvisa.value ? r.avvisati ?? 0 : 0, centro: [g.capo.lon, g.capo.lat] })
  } catch (e) { errore.value = messaggioErrore(e, 'certificare la segnalazione') }
  inCorso.value = null
}
async function archivia() {
  const g = gruppo.value
  if (!g || inCorso.value) return
  inCorso.value = 'archivia'; errore.value = ''
  try {
    await Promise.all(g.membri.map((m) => chiama(`/segnalazioni/${m.id}/archivia`, { method: 'POST' })))
    emit('archiviato', g.luogo)
  } catch (e) { errore.value = messaggioErrore(e, 'archiviare la segnalazione') }
  inCorso.value = null
}
const pct = (v: number) => `${Math.round(v * 100)}%`
</script>

<template>
  <div class="vista grid h-full min-h-0 gap-3 p-3">
    <!-- Elenco dei gruppi -->
    <section class="sospeso flex min-h-0 flex-col p-1.5" aria-labelledby="t-coda">
      <header class="flex items-center justify-between gap-2 px-2.5 pt-2 pb-2">
        <h2 id="t-coda" class="text-[1rem] font-semibold">Da verificare <span class="cifre ml-1 text-testo-3">{{ gruppi.length }}</span></h2>
        <button v-if="area" type="button" class="filtro h-7 rounded-full px-2.5 text-[.74rem] font-medium" :aria-pressed="!soloArea" @click="soloArea = !soloArea">
          {{ soloArea ? 'Solo ' + area.nome : 'Tutta la Sardegna' }}
        </button>
      </header>
      <TransitionGroup tag="ul" name="lista" class="cop-scroll relative flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-0.5">
        <li v-for="g in gruppi" :key="g.id">
          <button type="button" class="voce flex w-full gap-3 rounded-m p-2 text-left" :class="{ attiva: gruppo?.id === g.id }" @click="selezionato = g.id">
            <span class="miniatura relative size-14 shrink-0 overflow-hidden rounded-s bg-vetro-forte">
              <img v-if="g.pertinenti[0] || g.foto[0]" :src="(g.pertinenti[0] ?? g.foto[0])!.url" alt="" class="size-full object-cover" loading="lazy">
              <component :is="g.fuoco ? Flame : Cloud" v-else class="absolute inset-0 m-auto size-5 text-testo-3" aria-hidden="true" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="flex items-center gap-2">
                <span class="truncate text-[.88rem] font-semibold">{{ g.luogo }}</span>
                <span class="cifre ml-auto shrink-0 text-[.72rem] text-testo-3">{{ fmtOre(g.prima, ora) }}</span>
              </span>
              <span class="mt-0.5 block text-[.74rem] text-testo-2">{{ g.fuoco ? 'Fuoco' : 'Fumo' }} · {{ g.membri.length }} {{ g.membri.length > 1 ? 'segnalazioni' : 'segnalazione' }} · {{ g.conferme }} conferme</span>
              <span class="mt-1 flex items-center gap-1.5 text-[.72rem] font-medium" :style="{ color: varPriorita(g.capo.priorita) }">
                <span class="size-1.5 rounded-full" :style="{ background: varPriorita(g.capo.priorita) }" />Priorità {{ etichettaPriorita(g.capo.priorita).toLowerCase() }}
                <span v-if="g.aff" class="truncate font-normal text-testo-3">· {{ g.aff.etichetta.toLowerCase() }}</span>
              </span>
            </span>
          </button>
        </li>
      </TransitionGroup>
      <div v-if="!gruppi.length" class="m-auto flex max-w-[240px] flex-col items-center px-4 py-10 text-center">
        <Inbox class="size-6 text-testo-3" aria-hidden="true" />
        <p class="mt-2 text-[.88rem] font-medium">Nessuna segnalazione da verificare</p>
        <p class="mt-1 text-[.78rem] text-testo-3">Quando un cittadino segnala fuoco o fumo{{ area ? ` nell'area di ${area.nome}` : '' }}, compare qui con foto e conferme dei vicini.</p>
        <button v-if="fuoriArea && soloArea" type="button" class="secondario mt-3 h-9 px-4 text-[.8rem]" @click="soloArea = false">Mostra le altre {{ fuoriArea }} in Sardegna</button>
      </div>
    </section>

    <!-- Foto: solo quelle pertinenti in primo piano -->
    <section class="sospeso flex min-h-0 flex-col overflow-hidden p-3" aria-labelledby="t-foto">
      <Transition name="dettaglio" mode="out-in">
        <div v-if="gruppo" :key="gruppo.id" class="flex min-h-0 flex-1 flex-col">
          <header class="flex items-start justify-between gap-3 px-1 pb-3">
            <div class="min-w-0">
              <h2 id="t-foto" class="text-[1.2rem] leading-tight font-semibold tracking-[-0.01em]">{{ gruppo.fuoco ? 'Fuoco' : 'Fumo' }} a {{ gruppo.luogo }}</h2>
              <p class="cifre mt-0.5 flex items-center gap-1.5 text-[.8rem] text-testo-3"><MapPin class="size-3.5" aria-hidden="true" />{{ gruppo.capo.lat.toFixed(4) }}, {{ gruppo.capo.lon.toFixed(4) }} · prima segnalazione {{ fmtOre(gruppo.prima, ora) }} fa</p>
            </div>
          </header>

          <div v-if="fotoSel" class="foto relative min-h-0 flex-1 overflow-hidden rounded-m bg-fondo">
            <Transition name="foto">
              <img :key="fotoSel.url" :src="fotoSel.url" :alt="`Foto della segnalazione #${fotoSel.segnalazione}: ${fotoSel.motivo}`" class="absolute inset-0 size-full object-contain">
            </Transition>
            <p class="badge-ai absolute top-3 left-3 flex items-center gap-1.5 rounded-full py-1 pr-3 pl-2 text-[.76rem]">
              <Sparkles class="size-3.5 text-macchia" aria-hidden="true" />
              <span class="cifre font-semibold">{{ pct(fotoSel.pertinenza) }}</span>
              <span class="text-testo-2">{{ fotoSel.motivo }}</span>
            </p>
          </div>
          <div v-else class="foto flex min-h-0 flex-1 flex-col items-center justify-center rounded-m bg-vetro text-center">
            <ImageOff class="size-6 text-testo-3" aria-hidden="true" />
            <p class="mt-2 text-[.86rem] font-medium">Nessuna foto pertinente</p>
            <p class="mt-1 max-w-[300px] text-[.78rem] text-testo-3">Decidi su conferme e affidabilità, o manda una pattuglia a verificare.</p>
          </div>

          <div v-if="gruppo.pertinenti.length > 1" class="mt-2.5 flex gap-2 overflow-x-auto pb-0.5">
            <button v-for="f in gruppo.pertinenti" :key="f.url" type="button" class="pollice relative h-16 w-24 shrink-0 overflow-hidden rounded-s" :class="{ attiva: fotoSel?.url === f.url }" :aria-label="`Foto ${pct(f.pertinenza)}: ${f.motivo}`" @click="fotoSel = f">
              <img :src="f.url" alt="" class="size-full object-cover">
              <span class="cifre absolute right-1 bottom-1 rounded-full bg-black/60 px-1.5 text-[.66rem] font-semibold text-white">{{ pct(f.pertinenza) }}</span>
            </button>
          </div>

          <div v-if="gruppo.scartate.length" class="mt-2.5">
            <button type="button" class="flex items-center gap-1.5 text-[.78rem] text-testo-3 hover:text-testo-2" :aria-expanded="mostraScartate" @click="mostraScartate = !mostraScartate">
              <ChevronDown class="size-3.5 transition-transform duration-200" :class="{ '-rotate-90': !mostraScartate }" aria-hidden="true" />
              {{ gruppo.scartate.length }} {{ gruppo.scartate.length > 1 ? 'foto scartate' : 'foto scartata' }} dalla selezione AI
            </button>
            <div class="scartate-wrap" :class="{ aperto: mostraScartate }">
              <div class="min-h-0">
                <ul class="flex gap-2 pt-2">
                  <li v-for="f in gruppo.scartate" :key="f.url" class="flex w-56 items-center gap-2.5 rounded-s bg-vetro p-1.5">
                    <img :src="f.url" alt="" class="h-11 w-14 shrink-0 rounded-[4px] object-cover opacity-60 grayscale">
                    <span class="min-w-0 text-[.72rem] leading-snug"><span class="cifre font-semibold text-testo-2">{{ pct(f.pertinenza) }}</span> <span class="text-testo-3">{{ f.motivo }}</span></span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <ul v-if="gruppo.note.length" class="mt-3 flex flex-col gap-1.5">
            <li v-for="(n, k) in gruppo.note" :key="k" class="flex gap-2 text-[.8rem] text-testo-2"><Quote class="mt-0.5 size-3.5 shrink-0 text-testo-3" aria-hidden="true" />{{ n }}</li>
          </ul>
        </div>
      </Transition>
    </section>

    <!-- Validazione e decisione -->
    <section class="sospeso flex min-h-0 flex-col p-3" aria-labelledby="t-valida">
      <template v-if="gruppo">
        <h2 id="t-valida" class="px-1 text-[1rem] font-semibold">Validazione</h2>
        <div class="cop-scroll mt-2 min-h-0 flex-1 overflow-y-auto">
          <ul class="flex flex-col gap-1">
            <li v-for="s in segnali" :key="s.titolo" class="flex items-center gap-3 rounded-m px-1.5 py-2">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-s" :class="s.forte ? 'bg-macchia/15 text-macchia' : s.debole ? 'bg-ambra/15 text-ambra' : 'bg-vetro-forte text-testo-3'">
                <component :is="s.icona" class="size-4" aria-hidden="true" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block text-[.82rem]">{{ s.titolo }}</span>
                <span class="block truncate text-[.72rem] text-testo-3">{{ s.nota }}</span>
              </span>
              <span class="cifre text-[1.05rem] font-semibold">{{ s.valore }}</span>
            </li>
          </ul>

          <div v-if="gruppo.aff" class="vetro mt-2 p-3">
            <div class="flex items-baseline justify-between text-[.8rem]"><span>Affidabilità della comunità</span><span class="cifre font-semibold">{{ pct(gruppo.aff.valore) }}</span></div>
            <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-vetro-forte"><div class="metro h-full rounded-full bg-macchia" :style="{ width: pct(gruppo.aff.valore) }" /></div>
            <p class="mt-1.5 text-[.72rem] text-testo-3">{{ gruppo.aff.etichetta }}: conferme pesate per l'affidabilità storica di chi risponde</p>
          </div>
          <div class="vetro mt-2 flex items-center justify-between p-3 text-[.8rem]">
            <span>Priorità calcolata</span>
            <span class="cifre font-semibold" :style="{ color: varPriorita(gruppo.capo.priorita) }">{{ gruppo.capo.priorita }} · {{ etichettaPriorita(gruppo.capo.priorita) }}</span>
          </div>
        </div>

        <div class="mt-3 border-t border-bordo pt-3">
          <label class="flex cursor-pointer items-start gap-2.5 px-1 pb-3 text-[.8rem]">
            <input v-model="avvisa" type="checkbox" class="mt-0.5 size-4 accent-[var(--brace)]">
            <span>Avvisa chi è entro 5 km<span class="block text-[.72rem] text-testo-3">notifica push dall'app ai residenti e a chi monitora la zona</span></span>
          </label>
          <p v-if="errore" class="mb-2 px-1 text-[.78rem] text-brace" role="alert">{{ errore }}</p>
          <button type="button" class="primario flex h-11 w-full items-center justify-center gap-2 text-[.9rem]" :disabled="!!inCorso" @click="certifica">
            <ShieldCheck class="size-4" aria-hidden="true" />{{ inCorso === 'certifica' ? 'Certificazione...' : 'Certifica incendio' }}
          </button>
          <button type="button" class="secondario mt-2 flex h-10 w-full items-center justify-center gap-2 text-[.84rem]" :disabled="!!inCorso" @click="archivia">
            <OctagonX class="size-4" aria-hidden="true" />{{ inCorso === 'archivia' ? 'Archiviazione...' : 'Falso allarme' }}
          </button>
          <p class="mt-2 px-1 text-[.7rem] leading-snug text-testo-3">Certificato, compare come incendio nella mappa dei cittadini.</p>
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.vista { grid-template-columns: minmax(280px, 340px) minmax(0, 1fr) minmax(300px, 360px); }
@media (max-width: 1100px) { .vista { grid-template-columns: 1fr; grid-auto-rows: minmax(320px, auto); overflow-y: auto; } }
.voce { transition: background-color 150ms ease; }
@media (hover: hover) { .voce:hover { background: var(--vetro); } }
.voce.attiva { background: var(--vetro-forte); box-shadow: inset 0 0 0 1px var(--bordo-luce); }
.filtro { background: var(--vetro); color: var(--testo-2); border: 1px solid var(--bordo); transition: background-color 150ms ease; }
.filtro:hover { background: var(--vetro-forte); }
.foto { min-height: 240px; }
.badge-ai { background: rgba(8, 10, 14, 0.72); color: #f3f1ec; backdrop-filter: blur(12px); max-width: calc(100% - 24px); }
.badge-ai .text-testo-2 { color: #c9c5bc; }
.pollice { outline: 2px solid transparent; outline-offset: 2px; transition: outline-color 150ms ease, opacity 150ms ease; opacity: 0.7; }
.pollice.attiva { outline-color: var(--brace); opacity: 1; }
.pollice:hover { opacity: 1; }
.scartate-wrap { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 240ms var(--ease-out); }
.scartate-wrap.aperto { grid-template-rows: 1fr; }
.scartate-wrap > div { overflow: hidden; }
.metro { transition: width 500ms var(--ease-out); }
.foto-enter-active, .foto-leave-active { transition: opacity 220ms ease, filter 220ms ease; }
.foto-enter-from, .foto-leave-to { opacity: 0; filter: blur(4px); }
.dettaglio-enter-active { transition: opacity 220ms ease, transform 260ms var(--ease-out); }
.dettaglio-leave-active { transition: opacity 120ms ease; }
.dettaglio-enter-from { opacity: 0; transform: translateY(6px); }
.dettaglio-leave-to { opacity: 0; }
.lista-move { transition: transform 280ms var(--ease-out); }
.lista-leave-active { transition: opacity 200ms ease, transform 200ms ease; position: absolute; width: 100%; }
.lista-leave-to { opacity: 0; transform: translateX(-12px); }
.lista-enter-active { transition: opacity 260ms ease, transform 300ms var(--ease-out); }
.lista-enter-from { opacity: 0; transform: translateY(-6px); }
</style>
