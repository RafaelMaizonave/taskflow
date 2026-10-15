<script setup lang="ts">
import SelectMenu from '../ui/SelectMenu.vue'
import type { TaskStatus } from '../../types'

defineProps<{ status: TaskStatus; title: string; disabled?: boolean }>()
const emit = defineEmits<{ change: [status: TaskStatus] }>()
const options = [
  { value: 'backlog', label: 'Backlog', tone: 'backlog' },
  { value: 'in_progress', label: 'Em andamento', tone: 'in_progress' },
  { value: 'done', label: 'Concluída', tone: 'done' },
]
</script>

<template>
  <SelectMenu
    :model-value="status"
    :label="`Alterar status de ${title}`"
    :options="options"
    :disabled="disabled"
    @update:model-value="emit('change', $event as TaskStatus)"
  />
</template>
