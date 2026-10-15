<script setup lang="ts">
import { CheckCircle2, X, XCircle } from '@lucide/vue'
import { useToasts } from '../../composables/useToasts'

const { toasts, dismiss } = useToasts()
</script>

<template>
  <div
    class="toast-viewport"
    aria-live="polite"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="toast"
      :class="`toast--${toast.type}`"
    >
      <CheckCircle2
        v-if="toast.type === 'success'"
        :size="20"
      />
      <XCircle
        v-else
        :size="20"
      />
      <span>{{ toast.message }}</span>
      <button
        type="button"
        aria-label="Fechar aviso"
        @click="dismiss(toast.id)"
      >
        <X :size="17" />
      </button>
    </div>
  </div>
</template>
