<script setup lang="ts">
// Finestra che sale dal basso: tocco fuori o Esc la chiudono, il focus passa al suo interno.
// La maniglia in alto regola l'altezza trascinando (useAltezzaPannello); trascinata in fondo, chiude.
const props = defineProps<{ modelValue: boolean; titolo?: string }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()
const el = ref<HTMLElement>()

const chiudi = () => emit('update:modelValue', false)
const tasto = (e: KeyboardEvent) => { if (e.key === 'Escape' && props.modelValue) chiudi() }
const { stile, maniglia, reset } = useAltezzaPannello({ min: 150, chiudi })

onMounted(() => window.addEventListener('keydown', tasto))
onBeforeUnmount(() => window.removeEventListener('keydown', tasto))
watch(() => props.modelValue, (v) => { if (v) { reset(); nextTick(() => el.value?.focus({ preventScroll: true })) } })
</script>

<template>
  <Teleport to="body">
    <Transition name="foglio">
      <div v-if="modelValue" class="velo" @click.self="chiudi">
        <div ref="el" class="foglio outline-none" role="dialog" aria-modal="true" :aria-label="titolo" tabindex="-1" :style="stile">
          <div class="maniglia-area" role="button" tabindex="0" aria-label="Regola l'altezza della finestra" v-bind="maniglia"><div class="maniglia" /></div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
