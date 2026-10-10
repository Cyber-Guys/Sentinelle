<script setup lang="ts">
// Controllo segmentato delle schede del box Segnalazioni (cruscotto: colonna su desktop, foglio su telefono).
type IdScheda = 'nuova' | 'confermata' | 'archiviata'
defineProps<{ schede: readonly { id: IdScheda; etichetta: string }[]; conteggi: Record<IdScheda, number>; grande?: boolean }>()
const scheda = defineModel<IdScheda>({ required: true })
const nome = useId()
</script>

<template>
  <div class="flex rounded-full bg-vetro p-0.5 ring-1 ring-bordo" role="radiogroup" aria-label="Stato delle segnalazioni">
    <label v-for="f in schede" :key="f.id" class="flex flex-1 cursor-pointer items-center justify-center gap-1.5 rounded-full font-medium whitespace-nowrap transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-cielo" :class="[grande ? 'h-11 text-[.8rem]' : 'h-8 text-[.74rem]', scheda === f.id ? 'bg-vetro-forte text-testo ring-1 ring-bordo-luce' : 'text-testo-2 hover:text-testo']">
      <input v-model="scheda" type="radio" :name="nome" :value="f.id" class="sr-only" />{{ f.etichetta }}<span class="cifre text-testo-3">{{ conteggi[f.id] }}</span>
    </label>
  </div>
</template>
