<script setup lang="ts">
import { Check, X as Xicon, Loader2, Info, ThumbsUp, ThumbsDown } from '@lucide/vue'

// Blocco di voto condiviso da avviso di prossimita' e popup: chi l'ha confermato (dischi impilati, mai nomi),
// misuratore di affidabilita', due pulsanti da pollice; dopo il voto diventa la conferma animata.
const props = defineProps<{ s: Condivisa; motivo: string | null; inCorso: boolean; errore: string; grande?: boolean }>()
const emit = defineEmits<{ vota: [voto: 'ancora' | 'finito'] }>()

const dischi = computed(() => Math.min(props.s.conferme, 4))
const tinte = ['var(--brace)', 'var(--ambra)', 'var(--cielo)', 'var(--macchia)']
const ultimo = ref<'ancora' | 'finito' | null>(null)
function premi(v: 'ancora' | 'finito') { ultimo.value = v; emit('vota', v) }
</script>

<template>
  <div>
    <p class="flex items-center gap-2 text-[.8rem] leading-snug">
      <span v-if="dischi" class="flex shrink-0 -space-x-1.5" aria-hidden="true">
        <span v-for="i in dischi" :key="i" class="size-4 rounded-full ring-2 ring-fondo-2" :style="{ background: `color-mix(in srgb, ${tinte[(i - 1) % 4]} 70%, var(--fondo-3))` }" />
      </span>
      <span class="text-testo-2">
        <template v-if="s.conferme"><span class="cifre font-semibold text-testo">{{ s.conferme }}</span> {{ s.conferme === 1 ? 'cittadino l\'ha confermato' : 'cittadini l\'hanno confermato' }}</template>
        <template v-else>Nessuna conferma ancora: sii il primo</template>
        <template v-if="s.smentite"> · <span class="cifre">{{ s.smentite }}</span> dice che non c'è più</template>
      </span>
    </p>
    <MisuratoreAff class="mt-2.5" :valore="s.affidabilita.valore" :livello="s.affidabilita.livello" />

    <div aria-live="polite">
      <div v-if="s.mio_voto" class="voto-fatto mt-3 flex items-center gap-3 rounded-m p-2.5" :class="s.mio_voto === 'ancora' ? 'text-brace' : 'text-macchia'">
        <svg class="spunta size-9 shrink-0" viewBox="0 0 36 36" aria-hidden="true">
          <circle cx="18" cy="18" r="16" fill="none" stroke="currentColor" stroke-width="2" opacity=".25" />
          <circle class="spunta-anello" cx="18" cy="18" r="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
          <path class="spunta-segno" d="M11 18.5l4.6 4.6L25 13.6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <div class="min-w-0 leading-snug">
          <p class="text-[.9rem] font-semibold text-testo">
            <template v-if="s.mio_voto === 'ancora' && s.conferme <= 1">Grazie: sei il primo a confermarlo</template>
            <template v-else-if="s.mio_voto === 'ancora'">Grazie: ora siete in <span class="cifre">{{ s.conferme }}</span></template>
            <template v-else>Grazie: segnato come non più visibile</template>
          </p>
          <p class="text-[.74rem] text-testo-2">+10 punti se gli operatori {{ s.mio_voto === 'ancora' ? 'la confermano' : 'la chiudono come spenta' }}</p>
        </div>
      </div>
      <template v-else>
        <div class="mt-3 grid grid-cols-2 gap-2">
          <button type="button" class="voto-ancora flex items-center justify-center gap-2 font-semibold" :class="grande ? 'h-14 text-[.95rem]' : 'h-11 text-[.84rem]'" :disabled="!!motivo || inCorso" @click="premi('ancora')">
            <Loader2 v-if="inCorso && ultimo === 'ancora'" class="size-5 animate-spin" aria-hidden="true" /><ThumbsUp v-else class="size-5" aria-hidden="true" />C'è ancora
          </button>
          <button type="button" class="secondario flex items-center justify-center gap-2 font-semibold" :class="grande ? 'h-14 text-[.95rem]' : 'h-11 text-[.84rem]'" :disabled="!!motivo || inCorso" @click="premi('finito')">
            <Loader2 v-if="inCorso && ultimo === 'finito'" class="size-5 animate-spin" aria-hidden="true" /><ThumbsDown v-else class="size-5 text-macchia" aria-hidden="true" />Non c'è più
          </button>
        </div>
        <p v-if="motivo" class="mt-2 flex items-start gap-1.5 text-[.74rem] leading-snug text-testo-3"><Info class="mt-px size-3.5 shrink-0" aria-hidden="true" />{{ motivo }}</p>
      </template>
      <p v-if="errore" class="mt-2 flex items-start gap-1.5 rounded-m bg-brace/10 px-2.5 py-2 text-[.78rem] leading-snug text-brace" role="alert"><Xicon class="mt-px size-3.5 shrink-0" aria-hidden="true" />{{ errore }}</p>
    </div>
  </div>
</template>

<style>
.voto-ancora {
  border-radius: var(--radius-ctrl);
  color: var(--brace);
  background: color-mix(in srgb, var(--brace) 14%, var(--vetro-forte));
  border: 1px solid color-mix(in srgb, var(--brace) 45%, transparent);
  transition: background-color .15s ease, scale .12s ease;
}
.voto-ancora:hover:not(:disabled) { background: color-mix(in srgb, var(--brace) 22%, var(--vetro-forte)); }
.voto-ancora:disabled { opacity: .45; }
.voto-fatto { background: color-mix(in srgb, currentColor 10%, var(--vetro-forte)); animation: voto-entra .35s cubic-bezier(.22, 1, .36, 1); }
.spunta-anello { stroke-dasharray: 101; stroke-dashoffset: 101; transform: rotate(-90deg); transform-origin: center; animation: spunta-traccia .5s ease-out forwards; }
.spunta-segno { stroke-dasharray: 24; stroke-dashoffset: 24; animation: spunta-traccia .32s .38s ease-out forwards; }
@keyframes spunta-traccia { to { stroke-dashoffset: 0; } }
@keyframes voto-entra { from { opacity: 0; scale: .96; } }
</style>
