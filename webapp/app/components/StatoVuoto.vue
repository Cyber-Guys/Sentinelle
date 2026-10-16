<!-- Schermata vuota: dice cosa succedera' e offre l'azione, non solo "nessun dato". -->
<template>
  <div class="flex flex-col items-center gap-3 px-6 py-8 text-center">
    <span class="grid size-16 place-items-center rounded-full bg-vuoto text-testo-2"><slot name="icona" /></span>
    <p class="sottotitolo"><slot name="titolo" /></p>
    <p class="tenue max-w-[19rem] text-lg"><slot /></p>
    <div class="mt-1 w-full max-w-[19rem]"><slot name="azione" /></div>
  </div>
</template>
