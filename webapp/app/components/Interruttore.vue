<script setup lang="ts">
defineProps<{ modelValue: boolean; nome: string }>()
defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <button type="button" role="switch" class="interruttore" :aria-checked="modelValue" :aria-label="nome" @click="$emit('update:modelValue', !modelValue)" />
</template>
