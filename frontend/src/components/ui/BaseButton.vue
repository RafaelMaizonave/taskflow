<script setup lang="ts">
import { LoaderCircle } from '@lucide/vue'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    type?: 'button' | 'submit'
    loading?: boolean
    block?: boolean
    disabled?: boolean
  }>(),
  { variant: 'primary', size: 'md', type: 'button', loading: false },
)
</script>

<template>
  <button
    :type="type"
    class="btn"
    :class="[`btn--${variant}`, `btn--${size}`, { 'btn--block': block }]"
    :disabled="disabled || loading"
  >
    <LoaderCircle
      v-if="loading"
      :size="18"
      class="spin"
    />
    <slot />
  </button>
</template>
