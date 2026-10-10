<script setup lang="ts">
import { Layers, X, Flame } from '@lucide/vue'

// Pulsante "livelli" della mappa (come Google Maps / Apple Maps).
// App: sezione "Incendi storici" a radio (`filtri` + v-model). Cruscotto: sezioni a interruttore nello slot.
export interface FiltroStorico { id: string; etichetta: string; breve: string; dettaglio: string }

const props = defineProps<{ filtri?: readonly FiltroStorico[]; badge?: string; descrizione?: string }>()
const filtro = defineModel<string>()
// `acceso` (opzionale): se passato la sezione "Incendi storici" ha un interruttore on/off (cruscotto); nell'app e' sempre attiva
const acceso = defineModel<boolean | undefined>('acceso', { default: undefined })
const conInterruttore = computed(() => acceso.value !== undefined)
const mostra = computed(() => !conInterruttore.value || acceso.value)

// aperto esposto come v-model:aperto (opzionale): il cruscotto sposta la scheda dettaglio quando il pannello e' aperto
const aperto = defineModel<boolean>('aperto', { default: false })
const radice = ref<HTMLElement | null>(null)
const pulsante = ref<HTMLButtonElement | null>(null)
const pannello = ref<HTMLElement | null>(null)
const attivo = computed(() => props.filtri?.find((f) => f.id === filtro.value))
const testoBadge = computed(() => props.badge ?? attivo.value?.breve)

async function alterna() {
  aperto.value = !aperto.value
  if (aperto.value) {
    await nextTick()
    const p = pannello.value
    const primo = p?.querySelector<HTMLInputElement>('input:checked') ?? p?.querySelector<HTMLInputElement>('input')
    primo?.focus()
  }
}
function chiudi(rifocalizza = false) {
  if (!aperto.value) return
  aperto.value = false
  if (rifocalizza) pulsante.value?.focus()
}
// resta aperto dopo la scelta (si vede il cambio sulla mappa); si chiude toccando fuori o con Esc
const fuori = (e: PointerEvent) => { if (radice.value && !radice.value.contains(e.target as Node)) chiudi() }
const tasto = (e: KeyboardEvent) => { if (e.key === 'Escape') chiudi(true) }
onMounted(() => { document.addEventListener('pointerdown', fuori, true); document.addEventListener('keydown', tasto) })
onBeforeUnmount(() => { document.removeEventListener('pointerdown', fuori, true); document.removeEventListener('keydown', tasto) })
</script>

<template>
  <div ref="radice">
    <button
      ref="pulsante"
      type="button"
      class="pillola relative flex size-11 items-center justify-center transition-colors hover:bg-vetro-forte"
      :class="aperto && 'bg-vetro-forte'"
      :aria-expanded="aperto"
      aria-controls="pannello-livelli"
      :aria-label="`Livelli della mappa · ${descrizione ?? `incendi storici: ${attivo?.etichetta ?? ''}`}`"
      @click="alterna"
    >
      <Layers class="size-[18px] text-testo" aria-hidden="true" />
      <span v-if="testoBadge" class="cifre pointer-events-none absolute -bottom-1.5 left-1/2 -translate-x-1/2 rounded-full border border-bordo-luce bg-fondo-3 px-1.5 text-[.6rem] leading-[14px] font-semibold whitespace-nowrap text-ambra shadow-sm" aria-hidden="true">{{ testoBadge }}</span>
    </button>

    <Transition name="livelli">
      <section
        v-if="aperto"
        id="pannello-livelli"
        ref="pannello"
        class="sospeso absolute top-0 right-[calc(100%+.5rem)] w-[min(17.5rem,calc(100vw-5.5rem))] origin-top-right p-3"
        aria-labelledby="titolo-livelli"
      >
        <div class="mb-2 flex items-center justify-between gap-2 pl-1">
          <h2 id="titolo-livelli" class="text-[.95rem] font-semibold">Livelli</h2>
          <button type="button" aria-label="Chiudi i livelli" class="secondario tocco flex size-8 shrink-0 items-center justify-center" @click="chiudi(true)"><X class="size-4" aria-hidden="true" /></button>
        </div>

        <fieldset v-if="filtri" :class="conInterruttore && 'mb-2'">
          <legend v-if="!conInterruttore" class="etichetta mb-1.5 pl-1">Incendi storici</legend>
          <label v-else class="mb-1 flex min-h-11 cursor-pointer items-center gap-3 rounded-m border border-transparent px-3 py-2 transition-colors hover:bg-vetro has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo">
            <input v-model="acceso" type="checkbox" role="switch" class="sr-only" />
            <Flame class="size-4 shrink-0 text-brace" aria-hidden="true" />
            <span class="min-w-0 flex-1 leading-tight">
              <span class="block text-[.86rem] font-semibold">Incendi storici</span>
              <span class="block text-[.72rem] text-testo-2">Perimetri CFVA, dal 2015</span>
            </span>
            <span class="interruttore" :class="acceso && 'acceso'" aria-hidden="true" />
          </label>
          <div v-if="mostra" class="space-y-1">
            <label
              v-for="f in filtri"
              :key="f.id"
              class="flex min-h-11 cursor-pointer items-center gap-3 rounded-m border px-3 py-2 transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo"
              :class="filtro === f.id ? 'border-bordo-luce bg-vetro-forte' : 'border-transparent hover:bg-vetro'"
            >
              <input v-model="filtro" type="radio" name="filtro-storico" :value="f.id" class="sr-only" />
              <span class="flex size-4 shrink-0 items-center justify-center rounded-full border" :class="filtro === f.id ? 'border-brace' : 'border-bordo-luce'" aria-hidden="true">
                <span v-if="filtro === f.id" class="size-2 rounded-full bg-brace" />
              </span>
              <span class="min-w-0 flex-1 leading-tight">
                <span class="block text-[.86rem] font-semibold">{{ f.etichetta }}</span>
                <span class="block text-[.72rem] text-testo-2">{{ f.dettaglio }}</span>
              </span>
            </label>
          </div>
          <!-- legenda del colore per anno: ambra (vecchi) -> brace (recenti) -->
          <div v-if="mostra" class="mt-3 px-1" aria-hidden="true">
            <div class="legenda-storico h-1.5 rounded-full" />
            <div class="cifre mt-1 flex justify-between text-[.66rem] text-testo-3"><span>2015</span><span>2020</span><span>2025</span></div>
          </div>
          <p v-if="mostra" class="sr-only">Colore dei perimetri: da ambra per gli incendi piu' vecchi a brace per i piu' recenti.</p>
        </fieldset>
        <slot />
      </section>
    </Transition>
  </div>
</template>

<style>
.legenda-storico { background: linear-gradient(90deg, #c99a4a, #ff8a3d, #ff4a1f); }
html[data-tema='chiaro'] .legenda-storico { background: linear-gradient(90deg, #e2b45a, #ef7a2e, #d92d17); }
.livelli-enter-active { transition: opacity .18s ease-out, scale .18s cubic-bezier(.22, 1, .36, 1); }
.livelli-leave-active { transition: opacity .12s ease-in, scale .12s ease-in; }
.livelli-enter-from, .livelli-leave-to { opacity: 0; scale: .92; }
</style>
