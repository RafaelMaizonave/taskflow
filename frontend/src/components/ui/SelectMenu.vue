<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Check, ChevronDown, LoaderCircle } from '@lucide/vue'

const props = withDefaults(defineProps<{
  modelValue: string
  label: string
  options: readonly { value: string; label: string; tone?: string }[]
  disabled?: boolean
  variant?: 'badge' | 'filter'
}>(), { variant: 'badge' })
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const selected = computed(() => props.options.find(option => option.value === props.modelValue))
const trigger = ref<HTMLButtonElement | null>(null)
const menu = ref<HTMLElement | null>(null)
const open = ref(false)
const position = ref({ top: '0px', left: '0px', width: '184px' })

function close(restoreFocus = false) {
  open.value = false
  if (restoreFocus) trigger.value?.focus()
}
function placeMenu() {
  const bounds = trigger.value?.getBoundingClientRect()
  if (!bounds) return
  const width = Math.min(window.innerWidth - 16, Math.max(184, props.variant === 'filter' ? bounds.width : 184))
  const height = menu.value?.offsetHeight || props.options.length * 38 + 12
  position.value = {
    width: `${width}px`,
    left: `${Math.max(8, Math.min(bounds.left, window.innerWidth - width - 8))}px`,
    top: `${bounds.bottom + height + 6 > window.innerHeight ? Math.max(8, bounds.top - height - 6) : bounds.bottom + 6}px`,
  }
}
async function show() {
  if (props.disabled) return
  if (open.value) { close(); return }
  placeMenu()
  open.value = true
  await nextTick()
  placeMenu()
  menu.value?.querySelector<HTMLButtonElement>('[aria-checked="true"]')?.focus()
}
function choose(value: string) {
  close(true)
  if (!props.disabled && value !== props.modelValue) emit('update:modelValue', value)
}
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') { event.preventDefault(); close(true); return }
  if (event.key === 'Tab') { close(true); return }
  const buttons = [...(menu.value?.querySelectorAll<HTMLButtonElement>('button') || [])]
  if (!buttons.length) return
  const index = buttons.indexOf(document.activeElement as HTMLButtonElement)
  let next: number
  if (event.key === 'ArrowDown') next = (index + 1) % buttons.length
  else if (event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = buttons.length - 1
  else return
  event.preventDefault()
  buttons[next]?.focus()
}
function outside(event: Event) {
  const target = event.target as Node
  if (!trigger.value?.contains(target) && !menu.value?.contains(target)) close()
}
function onResize() { close() }
function onScroll(event: Event) {
  if (open.value && !menu.value?.contains(event.target as Node)) placeMenu()
}
onMounted(() => {
  document.addEventListener('pointerdown', outside)
  window.addEventListener('resize', onResize)
  window.addEventListener('scroll', onScroll, true)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', outside)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('scroll', onScroll, true)
})
watch(() => props.disabled, disabled => { if (disabled) close() })
</script>

<template>
  <button
    ref="trigger"
    type="button"
    :class="variant === 'badge' ? ['status-badge', 'task-status-trigger', `status-badge--${selected?.tone}`] : ['filter-group', 'filter-select-trigger']"
    :aria-label="label"
    aria-haspopup="menu"
    :aria-expanded="open"
    :aria-busy="disabled || undefined"
    :disabled="disabled"
    @dragstart.stop.prevent
    @click="show"
    @keydown.down.prevent="!open && show()"
    @keydown.up.prevent="!open && show()"
    @keydown.esc="close()"
  >
    <slot name="icon" />
    <i
      v-if="variant === 'badge'"
      aria-hidden="true"
    />
    <span :class="{ 'filter-select-label': variant === 'filter' }">{{ selected?.label }}</span>
    <LoaderCircle
      v-if="disabled"
      :size="12"
      class="spin"
      aria-hidden="true"
    />
    <ChevronDown
      v-else
      :size="12"
      aria-hidden="true"
    />
  </button>
  <Teleport to="body">
    <div
      v-if="open"
      ref="menu"
      class="select-menu"
      :style="position"
      role="menu"
      :aria-label="label"
      @keydown="onKeydown"
    >
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        role="menuitemradio"
        :aria-checked="modelValue === option.value"
        @click="choose(option.value)"
      >
        <span
          :class="option.tone ? ['status-badge', `status-badge--${option.tone}`] : 'select-menu-label'"
        >
          <i
            v-if="option.tone"
            aria-hidden="true"
          />{{ option.label }}
        </span>
        <Check
          v-if="modelValue === option.value"
          :size="15"
          aria-hidden="true"
        />
      </button>
    </div>
  </Teleport>
</template>
