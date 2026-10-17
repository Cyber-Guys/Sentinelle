<script setup lang="ts">
import { Flame, ChevronDown, Map as IconaMappa, Siren, Check, ShieldCheck, X, LayoutGrid } from '@lucide/vue'
import { DropdownMenuRoot, DropdownMenuTrigger, DropdownMenuPortal, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from 'reka-ui'
import MappaCop, { type Livelli } from '~/components/cop/MappaCop.vue'
import IngressoAree from '~/components/cop/IngressoAree.vue'
import PannelloLivelli from '~/components/cop/PannelloLivelli.vue'
import PannelloArea from '~/components/cop/PannelloArea.vue'
import SchedaIncendio from '~/components/cop/SchedaIncendio.vue'
import VistaSegnalazioni from '~/components/cop/VistaSegnalazioni.vue'
import { LIVELLI_CFD, dentro, type AreaCop, type Bollettino, type Incendio, type Statistiche, type LivelloCfd } from '~/composables/useCop'

/*
  Dashboard degli operatori COP (piano 2026-10-17-dashboard-cop). Ingresso con le 7 aree sulla stessa mappa,
  poi zoom sull'area scelta con livelli sovrapponibili e statistiche a destra; vista Segnalazioni per
  certificare le segnalazioni dei cittadini. Area e vista stanno nell'URL (?area=cagliari&vista=segnalazioni).
*/
useHead({ title: 'Dashboard COP · Sentinelle' })
const { chiama } = useApi()
const route = useRoute()
const router = useRouter()

const areaSel = computed(() => (typeof route.query.area === 'string' ? route.query.area : null))
const vista = computed(() => (route.query.vista === 'segnalazioni' ? 'segnalazioni' : 'mappa'))
const vai = (q: { area?: string | null; vista?: string | null }) => {
  const query: Record<string, string> = {}
  const a = q.area === undefined ? areaSel.value : q.area
  const v = q.vista === undefined ? vista.value : q.vista
  if (a) query.area = a
  if (v === 'segnalazioni') query.vista = v
  router.replace({ query })
}

// ---------------------------------------------------------------- dati

const VUOTO = { type: 'FeatureCollection', features: [] as any[] }
const aree = shallowRef<AreaCop[]>([])
const bollettini = shallowRef<{ oggi: Bollettino | null; domani: Bollettino | null }>({ oggi: null, domani: null })
const incendi = shallowRef<any>(VUOTO)
const vedette = shallowRef<any>(VUOTO)
const fuochi = shallowRef<any>(VUOTO)
const invasi = shallowRef<any>(VUOTO)
const basi = shallowRef<any>(VUOTO)
const segnalazioni = shallowRef<any[]>([])
const affidabilita = shallowRef<Record<number, any>>({})
const statistiche = shallowRef<Statistiche | null>(null)
const errore = ref('')

const area = computed(() => aree.value.find((a) => a.id === areaSel.value) ?? null)
const giorno = ref<'oggi' | 'domani'>('oggi')
const bollettino = computed(() => bollettini.value[giorno.value])
const livelli = ref<Livelli>({ rischio: true, incendi: true, spenti: true, storico: false, invasi: true, fuochi: false, vedette: true, basi: true, terra: true, aerei: true, segnalazioni: true })
const anni = ref<[number, number]>([2015, 2025])
// all'ingresso solo il quadro regionale: rischio e incendi; le risorse si accendono dentro l'area
const livelliMappa = computed<Livelli>(() => areaSel.value ? livelli.value
  : { rischio: true, incendi: true, spenti: false, storico: false, invasi: false, fuochi: false, vedette: false, basi: false, terra: false, aerei: false, segnalazioni: false })
const incendioSel = ref<string | null>(null)

async function caricaFissi() {
  try {
    const [a, oggi, domani, v, f, inv, b] = await Promise.all([
      chiama<any>('/cop/aree'), chiama<Bollettino>('/cop/bollettino'), chiama<Bollettino>('/cop/bollettino?giorno=domani'),
      chiama<any>('/cop/vedette'), chiama<any>('/cop/fuochi'), chiama<any>('/invasi'), chiama<any>('/basi'),
    ])
    aree.value = a.features.map((x: any) => ({ ...x.properties, geometria: x.geometry }))
    bollettini.value = { oggi, domani }
    vedette.value = v; fuochi.value = f; invasi.value = inv; basi.value = b
  } catch (e) { errore.value = messaggioErrore(e) }
}
async function caricaIncendi() { try { incendi.value = await chiama('/cop/incendi') } catch { /* resta l'ultimo stato */ } }
async function caricaSegnalazioni() {
  try {
    const [nuove, attive] = await Promise.all([chiama<any[]>('/segnalazioni?stato=nuova'), chiama<any[]>('/segnalazioni/attive')])
    segnalazioni.value = nuove.filter((s) => s.tipo !== 'area_a_rischio')
    affidabilita.value = Object.fromEntries(attive.map((s) => [s.id, s.affidabilita]))
  } catch { /* idem */ }
}
watch(areaSel, async (id) => {
  statistiche.value = null
  incendioSel.value = null
  if (id) try { statistiche.value = await chiama<Statistiche>(`/cop/statistiche?area=${id}`) } catch {}
}, { immediate: true })

// Flotta simulata: posizioni a t e t+10 s, interpolate lato client ogni mezzo secondo
let flottaDati: { t0: number; mezzi: any[] } = { t0: 0, mezzi: [] }
const flotta = shallowRef<any[]>([])
function muoviFlotta() {
  const f = Math.min(1.5, Math.max(0, (Date.now() / 1000 - flottaDati.t0) / 10))
  flotta.value = flottaDati.mezzi.map((x) => ({ ...x, lon: x.lon + (x.lon_poi - x.lon) * f, lat: x.lat + (x.lat_poi - x.lat) * f }))
}
async function caricaFlotta() {
  try { const d = await chiama<any>(`/flotta?t=${Math.floor(Date.now() / 1000)}`); flottaDati = { t0: d.t, mezzi: d.mezzi }; muoviFlotta() } catch {}
}

const ora = ref(Date.now())
const timer: ReturnType<typeof setInterval>[] = []
const { on } = useEventi()
const spegni: (() => void)[] = []
onMounted(() => {
  caricaFissi(); caricaIncendi(); caricaSegnalazioni(); caricaFlotta()
  timer.push(setInterval(caricaFlotta, 10000), setInterval(muoviFlotta, 500), setInterval(caricaIncendi, 20000),
    setInterval(caricaSegnalazioni, 30000), setInterval(() => (ora.value = Date.now()), 20000))
  for (const t of ['segnalazione_nuova', 'segnalazione_aggiornata', 'segnalazione_valutata']) spegni.push(on(t, () => { caricaSegnalazioni(); caricaIncendi() }))
})
onBeforeUnmount(() => { timer.forEach(clearInterval); spegni.forEach((f) => f()) })

// ---------------------------------------------------------------- derivati per area

const listaIncendi = computed<Incendio[]>(() => (incendi.value.features ?? []).map((f: any) => f.properties))
const incendiArea = computed(() => listaIncendi.value.filter((i) => i.area === areaSel.value))
const inArea = (p: [number, number]) => !!area.value && dentro(p, area.value.geometria)
const segnArea = computed(() => segnalazioni.value.filter((s) => inArea([s.lon, s.lat])))
const flottaArea = computed(() => flotta.value.filter((m) => inArea([m.lon, m.lat])))
const invasiArea = computed(() => (invasi.value.features ?? []).filter((f: any) => inArea(f.geometry.coordinates)))
const fuochiArea = computed(() => (fuochi.value.features ?? []).filter((f: any) => f.properties.area === areaSel.value))
const perArea = (conta: (a: AreaCop) => number) => Object.fromEntries(aree.value.map((a) => [a.id, conta(a)]))
const incendiPerArea = computed(() => perArea((a) => listaIncendi.value.filter((i) => i.area === a.id && i.stato === 'attivo').length))
const segnPerArea = computed(() => perArea((a) => segnalazioni.value.filter((s) => dentro([s.lon, s.lat], a.geometria)).length))
const conteggi = computed(() => ({
  incendi: listaIncendi.value.filter((i) => i.stato === 'attivo').length, spenti: listaIncendi.value.filter((i) => i.stato === 'spento').length,
  invasi: invasi.value.features.length, vedette: vedette.value.features.length, fuochi: fuochi.value.features.length,
  basi: basi.value.features.length, terra: flotta.value.filter((m) => m.categoria === 'terra').length,
  aerei: flotta.value.filter((m) => m.categoria === 'aereo').length, segnalazioni: segnalazioni.value.length,
}))
const allerta = (b: Bollettino | null): LivelloCfd => {
  if (!b) return 'verde'
  const lv = areaSel.value ? [b.per_area[areaSel.value]?.massimo] : Object.values(b.per_area).map((q) => q.massimo)
  return lv.includes('rosso') ? 'rosso' : lv.includes('arancione') ? 'arancione' : 'verde'
}

// ---------------------------------------------------------------- interazioni

const mappaRef = ref<InstanceType<typeof MappaCop>>()
const areaHover = ref<string | null>(null)
const incendio = computed(() => listaIncendi.value.find((i) => i.id === incendioSel.value) ?? null)
const segnSel = ref<number | null>(null)
const PANNELLO = 400

function scegliArea(id: string | null) { areaHover.value = null; vai({ area: id, vista: 'mappa' }) }
function apriIncendio(id: string) {
  incendioSel.value = id
  const i = listaIncendi.value.find((x) => x.id === id)
  if (i) mappaRef.value?.volaA(i.centro, 12.2)
}
function chiudiIncendio() { incendioSel.value = null; mappaRef.value?.inquadra() }
function apriSegnalazione(id: number) { segnSel.value = id; vai({ vista: 'segnalazioni' }) }

type Avviso = { testo: string; dettaglio?: string; azione?: { etichetta: string; fn: () => void } }
const avviso = ref<Avviso | null>(null)
let timerAvviso: ReturnType<typeof setTimeout> | undefined
function mostra(a: Avviso) { avviso.value = a; clearTimeout(timerAvviso); timerAvviso = setTimeout(() => (avviso.value = null), 7000) }

async function certificato(e: { luogo: string; avvisati: number; centro: [number, number] }) {
  await Promise.all([caricaSegnalazioni(), caricaIncendi()])
  mostra({
    testo: `Incendio certificato a ${e.luogo}`,
    dettaglio: e.avvisati ? `Visibile nell'app. Avvisate ${e.avvisati} persone entro 5 km.` : "Visibile nell'app dei cittadini.",
    azione: { etichetta: 'Vedi sulla mappa', fn: () => {
      vai({ vista: 'mappa' })
      const i = listaIncendi.value.find((x) => x.stato === 'attivo' && Math.abs(x.centro[0] - e.centro[0]) < 0.01 && Math.abs(x.centro[1] - e.centro[1]) < 0.01)
      nextTick(() => (i ? apriIncendio(i.id) : mappaRef.value?.volaA(e.centro)))
      avviso.value = null
    } },
  })
}
async function archiviato(luogo: string) { await caricaSegnalazioni(); mostra({ testo: `Segnalazione a ${luogo} archiviata come falso allarme` }) }

const chiusura = ref(false)
async function concludi(id: string) {
  chiusura.value = true
  try {
    await chiama(`/cop/incendi/${id}/concludi`, { method: 'POST' })
    await caricaIncendi()
    mostra({ testo: 'Incendio concluso', dettaglio: `L'area bruciata resta segnata come spenta per ${incendi.value.ore_area_spenta ?? 72} ore.` })
  } catch (e) { mostra({ testo: messaggioErrore(e, "chiudere l'incendio") }) }
  chiusura.value = false
}

function tasto(e: KeyboardEvent) {
  if (e.key !== 'Escape' || (e.target as HTMLElement)?.closest('[role="menu"]')) return
  if (incendioSel.value) chiudiIncendio()
  else if (vista.value === 'segnalazioni') vai({ vista: 'mappa' })
}
onMounted(() => window.addEventListener('keydown', tasto))
onBeforeUnmount(() => window.removeEventListener('keydown', tasto))
const orologio = computed(() => new Date(ora.value).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }))
</script>

<template>
  <div class="cop fixed inset-0 flex flex-col overflow-hidden">
    <!-- Barra superiore -->
    <header class="barra relative z-30 flex h-14 shrink-0 items-center gap-3 px-3 sm:px-4">
      <NuxtLink to="/dashboard" class="flex shrink-0 items-center gap-2.5" aria-label="Sentinelle, torna alla scelta dell'area" @click.prevent="scegliArea(null)">
        <span class="flex size-8 items-center justify-center rounded-[32%] bg-gradient-to-b from-[#f2581d] to-[#d33515] shadow-[0_6px_16px_-8px_rgba(255,90,31,.7),inset_0_1px_0_rgba(255,255,255,.2)]">
          <Flame class="size-4 text-white" aria-hidden="true" />
        </span>
        <span class="hidden text-[.95rem] font-semibold md:inline">Sentinelle</span>
      </NuxtLink>
      <span class="hidden h-5 w-px bg-bordo-luce sm:block" aria-hidden="true" />

      <DropdownMenuRoot :modal="false">
        <DropdownMenuTrigger class="selettore flex h-9 items-center gap-2 rounded-full pr-2.5 pl-3.5 text-[.88rem] font-semibold">
          {{ area ? `COP ${area.nome}` : 'Tutte le aree' }}
          <ChevronDown class="size-4 text-testo-3" aria-hidden="true" />
        </DropdownMenuTrigger>
        <DropdownMenuPortal>
          <DropdownMenuContent class="menu sospeso z-50 w-64 p-1.5" :side-offset="8" align="start">
            <DropdownMenuItem class="voce-menu" @select="scegliArea(null)"><LayoutGrid class="size-4 text-testo-3" aria-hidden="true" />Tutte le aree</DropdownMenuItem>
            <DropdownMenuSeparator class="my-1 h-px bg-bordo" />
            <DropdownMenuItem v-for="a in aree" :key="a.id" class="voce-menu" @select="scegliArea(a.id)">
              <span class="size-2 shrink-0 rounded-full" :style="{ background: LIVELLI_CFD[bollettini.oggi?.per_area[a.id]?.massimo ?? 'verde'].css }" aria-hidden="true" />
              <span class="flex-1">{{ a.nome }}</span>
              <Check v-if="a.id === areaSel" class="size-4 text-testo-2" aria-hidden="true" />
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenuPortal>
      </DropdownMenuRoot>

      <nav class="schede ml-1 flex rounded-full p-0.5" aria-label="Sezioni">
        <button type="button" class="scheda flex h-8 items-center gap-1.5 rounded-full px-3 text-[.82rem] font-medium" :aria-current="vista === 'mappa' ? 'page' : undefined" @click="vai({ vista: 'mappa' })">
          <IconaMappa class="size-4" aria-hidden="true" />Mappa
        </button>
        <button type="button" class="scheda flex h-8 items-center gap-1.5 rounded-full px-3 text-[.82rem] font-medium" :aria-current="vista === 'segnalazioni' ? 'page' : undefined" @click="vai({ vista: 'segnalazioni' })">
          <Siren class="size-4" aria-hidden="true" />Segnalazioni
          <span v-if="(area ? segnArea : segnalazioni).length" class="contatore cifre rounded-full px-1.5 text-[.7rem] font-semibold">{{ (area ? segnArea : segnalazioni).length }}</span>
        </button>
      </nav>

      <div class="ml-auto flex items-center gap-2.5">
        <div class="hidden items-center gap-1 rounded-full bg-vetro p-1 pr-1 lg:flex" :aria-label="`Bollettino CFD${area ? ` per ${area.nome}` : ' regionale'}`">
          <span class="px-2 text-[.74rem] text-testo-3">CFD</span>
          <span v-for="g in (['oggi', 'domani'] as const)" :key="g" class="flex h-7 items-center gap-1.5 rounded-full bg-vetro-forte px-2.5 text-[.76rem]">
            <span class="text-testo-3">{{ g === 'oggi' ? 'Oggi' : 'Domani' }}</span>
            <span class="size-2 rounded-full" :style="{ background: LIVELLI_CFD[allerta(bollettini[g])].css }" aria-hidden="true" />
            <span class="font-medium">{{ LIVELLI_CFD[allerta(bollettini[g])].breve }}</span>
          </span>
        </div>
        <span class="hidden items-center gap-2 text-[.8rem] text-testo-2 sm:flex"><span class="punto-vivo punto-verde" aria-hidden="true" /><span class="cifre">{{ orologio }}</span></span>
        <InterruttoreTema compatto class="!size-9" />
      </div>
    </header>

    <main class="relative min-h-0 flex-1">
      <MappaCop ref="mappaRef" :aree="aree" :area-sel="areaSel" :area-hover="areaHover" :bollettino="bollettino" :livelli="livelliMappa" :anni="anni"
        :incendi="incendi" :vedette="vedette" :fuochi="fuochi" :invasi="invasi" :basi="basi" :flotta="flotta" :segnalazioni="segnalazioni"
        :incendio-sel="incendioSel" :pad-destra="PANNELLO + 12" @scegli="scegliArea" @hover="areaHover = $event" @incendio="apriIncendio" @segnalazione="apriSegnalazione" />

      <!-- Ingresso: scelta dell'area -->
      <Transition name="ingresso">
        <div v-if="!areaSel && vista === 'mappa'" class="pointer-events-none absolute inset-y-4 left-4 z-10 flex items-start">
          <IngressoAree class="pointer-events-auto max-h-full" :aree="aree" :hover="areaHover" :oggi="bollettini.oggi" :domani="bollettini.domani"
            :incendi="incendiPerArea" :segnalazioni="segnPerArea" @scegli="scegliArea" @hover="areaHover = $event" />
        </div>
      </Transition>

      <!-- Area: livelli a sinistra, statistiche a destra -->
      <Transition name="livelli">
        <div v-if="areaSel && vista === 'mappa'" class="pointer-events-none absolute inset-y-3 left-3 z-10 hidden md:flex">
          <PannelloLivelli v-model:livelli="livelli" v-model:giorno="giorno" v-model:anni="anni" class="pointer-events-auto self-start" :conteggi="conteggi" />
        </div>
      </Transition>
      <Transition name="pannello">
        <aside v-if="area && vista === 'mappa'" class="pannello sospeso absolute top-3 right-3 bottom-3 z-10 flex flex-col overflow-hidden" :style="{ width: `min(${PANNELLO}px, calc(100% - 24px))` }" aria-label="Statistiche dell'area">
          <div class="cop-scroll min-h-0 flex-1 overflow-x-hidden overflow-y-auto p-3">
            <Transition name="scheda" mode="out-in">
              <SchedaIncendio v-if="incendio" :key="incendio.id" :incendio="incendio" :area="area.nome" :flotta="flotta" :invasi="invasi.features" :vedette="vedette.features"
                :ora="ora" :ore-area-spenta="incendi.ore_area_spenta ?? 72" :in-corso="chiusura" @indietro="chiudiIncendio" @concludi="concludi" />
              <PannelloArea v-else :key="area.id" :area="area" :bollettino="bollettino" :giorno="giorno" :incendi="incendiArea" :da-verificare="segnArea.length"
                :flotta="flotta" :flotta-area="flottaArea" :invasi="invasiArea" :fuochi="fuochiArea" :statistiche="statistiche" :ora="ora"
                @incendio="apriIncendio" @segnalazioni="vai({ vista: 'segnalazioni' })" />
            </Transition>
          </div>
        </aside>
      </Transition>

      <!-- Legenda del bollettino -->
      <Transition name="dissolvi">
        <div v-if="areaSel && vista === 'mappa' && livelli.rischio" class="legenda pillola absolute bottom-3 left-3 z-10 hidden items-center gap-3 py-1.5 pr-3.5 pl-3 text-[.74rem] md:flex">
          <span class="font-medium">CFD {{ giorno }}</span>
          <span v-for="l in (['verde', 'arancione', 'rosso'] as const)" :key="l" class="flex items-center gap-1.5 text-testo-2">
            <span class="size-2.5 rounded-full" :style="{ background: LIVELLI_CFD[l].css }" />{{ LIVELLI_CFD[l].etichetta.replace('Pericolo ', '') }}
          </span>
          <span class="text-testo-3">simulato</span>
        </div>
      </Transition>

      <!-- Segnalazioni -->
      <Transition name="vista">
        <div v-if="vista === 'segnalazioni'" class="sfondo-vista absolute inset-0 z-20">
          <VistaSegnalazioni v-model:selezionato="segnSel" :segnalazioni="segnalazioni" :affidabilita="affidabilita" :area="area" :ora="ora"
            @certificato="certificato" @archiviato="archiviato" />
        </div>
      </Transition>

      <p v-if="errore" class="pillola absolute top-4 left-1/2 z-40 -translate-x-1/2 px-4 py-2 text-[.82rem] text-brace" role="alert">{{ errore }}</p>

      <!-- Avviso dopo un'azione -->
      <Transition name="avviso">
        <div v-if="avviso" class="avviso sospeso absolute bottom-5 left-1/2 z-40 flex w-[min(520px,calc(100%-32px))] items-center gap-3 p-3 pl-3.5" role="status">
          <span class="flex size-9 shrink-0 items-center justify-center rounded-full bg-macchia/15 text-macchia"><ShieldCheck class="size-[18px]" aria-hidden="true" /></span>
          <span class="min-w-0 flex-1">
            <span class="block text-[.88rem] font-semibold">{{ avviso.testo }}</span>
            <span v-if="avviso.dettaglio" class="block text-[.78rem] text-testo-2">{{ avviso.dettaglio }}</span>
          </span>
          <button v-if="avviso.azione" type="button" class="secondario h-9 shrink-0 px-3.5 text-[.8rem]" @click="avviso.azione.fn">{{ avviso.azione.etichetta }}</button>
          <button type="button" class="flex size-8 shrink-0 items-center justify-center rounded-full text-testo-3 hover:bg-vetro-forte hover:text-testo" aria-label="Chiudi avviso" @click="avviso = null">
            <X class="size-4" aria-hidden="true" />
          </button>
        </div>
      </Transition>
    </main>
  </div>
</template>

<style scoped>
.selettore { background: var(--vetro); border: 1px solid var(--bordo); transition: background-color 150ms ease; }
.selettore:hover, .selettore[data-state='open'] { background: var(--vetro-forte); }
.schede { background: var(--vetro); }
.scheda { color: var(--testo-3); transition: background-color 160ms ease, color 160ms ease; }
.scheda:hover { color: var(--testo-2); }
.scheda[aria-current='page'] { background: var(--vetro-forte); color: var(--testo); box-shadow: inset 0 0 0 1px var(--bordo-luce); }
.contatore { background: color-mix(in srgb, var(--ambra) 22%, transparent); color: var(--ambra); }
.punto-verde { --pin: var(--macchia); }
.sfondo-vista { background: var(--fondo); }
.sfondo-vista::before { content: ''; position: absolute; inset: 0; background: var(--atmosfera); z-index: -1; }

/* menu delle aree: scala dal trigger (origine fornita da Reka) */
:global(.menu) { transform-origin: var(--reka-dropdown-menu-content-transform-origin); animation: menu-entra 160ms var(--ease-out); }
:global(.menu[data-state='closed']) { animation: menu-esce 100ms ease forwards; }
@keyframes menu-entra { from { opacity: 0; transform: scale(0.96); } }
@keyframes menu-esce { to { opacity: 0; transform: scale(0.98); } }
:global(.voce-menu) { display: flex; align-items: center; gap: 10px; height: 36px; padding: 0 10px; border-radius: var(--radius-m); font-size: .86rem; outline: none; cursor: pointer; }
:global(.voce-menu[data-highlighted]) { background: var(--vetro-forte); }

/* coreografia della scelta dell'area: la mappa vola (1,5 s), i pannelli entrano mentre arriva */
.ingresso-enter-active { transition: opacity 360ms ease, transform 420ms var(--ease-out); transition-delay: 150ms; }
.ingresso-leave-active { transition: opacity 200ms ease, transform 260ms var(--ease-out); }
.ingresso-enter-from, .ingresso-leave-to { opacity: 0; transform: translateX(-16px); }
.pannello-enter-active { transition: opacity 320ms ease, transform 520ms var(--ease-out); transition-delay: 420ms; }
.pannello-leave-active { transition: opacity 180ms ease, transform 220ms ease; }
.pannello-enter-from { opacity: 0; transform: translateX(28px); }
.pannello-leave-to { opacity: 0; transform: translateX(16px); }
.livelli-enter-active { transition: opacity 300ms ease, transform 420ms var(--ease-out); transition-delay: 620ms; }
.livelli-leave-active { transition: opacity 150ms ease; }
.livelli-enter-from { opacity: 0; transform: translateY(-8px); }
.livelli-leave-to { opacity: 0; }
.scheda-enter-active { transition: opacity 200ms ease, transform 280ms var(--ease-out); }
.scheda-leave-active { transition: opacity 120ms ease, transform 160ms ease; }
.scheda-enter-from { opacity: 0; transform: translateX(14px); }
.scheda-leave-to { opacity: 0; transform: translateX(-10px); }
.vista-enter-active { transition: opacity 240ms ease, transform 300ms var(--ease-out); }
.vista-leave-active { transition: opacity 160ms ease; }
.vista-enter-from { opacity: 0; transform: scale(0.99); }
.vista-leave-to { opacity: 0; }
.dissolvi-enter-active, .dissolvi-leave-active { transition: opacity 240ms ease; }
.dissolvi-enter-active { transition-delay: 700ms; }
.dissolvi-enter-from, .dissolvi-leave-to { opacity: 0; }
.avviso { translate: -50% 0; }
.avviso-enter-active { transition: opacity 220ms ease, transform 320ms var(--ease-out); }
.avviso-leave-active { transition: opacity 160ms ease, transform 200ms ease; }
.avviso-enter-from { opacity: 0; transform: translateY(12px) scale(0.98); }
.avviso-leave-to { opacity: 0; transform: translateY(6px); }
</style>
