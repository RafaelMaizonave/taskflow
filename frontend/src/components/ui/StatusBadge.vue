<script setup lang="ts">
import type { TaskPriority, TaskStatus } from '../../types'

const props = defineProps<{ value: TaskStatus | TaskPriority }>()
const labels: Record<string, string> = {
  backlog: 'Backlog',
  in_progress: 'Em andamento',
  done: 'Concluída',
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
}
</script>

<template>
  <span
    class="status-badge"
    :class="`status-badge--${props.value}`"
  >
    <i aria-hidden="true" />
    {{ labels[props.value] }}
  </span>
</template>
