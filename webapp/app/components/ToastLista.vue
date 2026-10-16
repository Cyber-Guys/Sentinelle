<script setup lang="ts">
import { CircleAlert, CircleCheck } from '@lucide/vue'

const { messaggi } = useToast()
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 top-3 z-50 mx-auto flex max-w-[30rem] flex-col items-center gap-2 px-3" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="m in messaggi" :key="m.id" class="toast pointer-events-auto" :class="{ 'toast-errore': m.errore }" role="status">
        <CircleAlert v-if="m.errore" class="size-5 flex-none" aria-hidden="true" />
        <CircleCheck v-else class="size-5 flex-none" aria-hidden="true" />
        <span>{{ m.testo }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>
