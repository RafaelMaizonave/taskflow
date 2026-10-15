<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { AlertTriangle } from '@lucide/vue'
import BaseButton from '../ui/BaseButton.vue'
import { useDialog } from '../../composables/useDialog'

const { dialog, close } = useDialog()
const panel = ref<HTMLElement | null>(null)
let previousFocus: HTMLElement | null = null

function keydown(event: KeyboardEvent) {
  if (!dialog.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    close(false)
    return
  }
  if (event.key !== 'Tab' || !panel.value) return
  const elements = panel.value.querySelectorAll<HTMLElement>(
    'button:not(:disabled)',
  )
  if (!elements.length) return
  const first = elements[0]!
  const last = elements[elements.length - 1]!
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  dialog,
  async (current) => {
    if (current) {
      previousFocus = document.activeElement as HTMLElement
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', keydown)
      await nextTick()
      const focusTarget =
        panel.value?.querySelector<HTMLElement>(
          current.mode === 'confirm'
            ? '[data-dialog-cancel]'
            : '[data-dialog-confirm]',
        ) ?? panel.value?.querySelector<HTMLElement>('button')
      focusTarget?.focus()
    } else {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', keydown)
      previousFocus?.focus()
      previousFocus = null
    }
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', keydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="dialog"
      class="app-dialog-layer"
      role="presentation"
    >
      <div
        class="app-dialog-scrim"
        @click="close(false)"
      />
      <section
        ref="panel"
        class="app-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="app-dialog-title"
        aria-describedby="app-dialog-message"
      >
        <div
          class="app-dialog__icon"
          :class="`app-dialog__icon--${dialog.variant || 'primary'}`"
          aria-hidden="true"
        >
          <AlertTriangle :size="22" />
        </div>
        <div class="app-dialog__body">
          <h2 id="app-dialog-title">
            {{ dialog.title }}
          </h2>
          <p id="app-dialog-message">
            {{ dialog.message }}
          </p>
        </div>
        <footer class="app-dialog__actions">
          <BaseButton
            v-if="dialog.mode === 'confirm'"
            variant="secondary"
            data-dialog-cancel
            @click="close(false)"
          >
            {{ dialog.cancelLabel }}
          </BaseButton>
          <BaseButton
            :variant="dialog.variant === 'danger' ? 'danger' : 'primary'"
            data-dialog-confirm
            @click="close(true)"
          >
            {{ dialog.confirmLabel }}
          </BaseButton>
        </footer>
      </section>
    </div>
  </Teleport>
</template>
