<script setup lang="ts">
import { CalendarDays, Pencil, Trash2 } from '@lucide/vue'
import StatusBadge from '../../components/ui/StatusBadge.vue'
import StatusQuickEdit from './StatusQuickEdit.vue'
import type { Task, TaskStatus } from '../../types'

defineProps<{ task: Task; board?: boolean; moving?: boolean }>()
const emit = defineEmits<{
  edit: [task: Task]
  remove: [task: Task]
  move: [task: Task, status: TaskStatus]
  dragstart: [task: Task]
}>()

function formatDate(value: string | null) {
  if (!value) return 'Sem prazo'
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: 'short',
  }).format(new Date(`${value}T12:00:00`))
}
</script>

<template>
  <article
    class="task-card"
    :class="{ 'task-card--board': board }"
    :draggable="board && !moving"
    @dragstart="emit('dragstart', task)"
  >
    <div class="task-card__main">
      <div>
        <strong>{{ task.title }}</strong>
        <p v-if="task.description">
          {{ task.description }}
        </p>
        <div class="task-tags">
          <span
            v-for="tag in task.tags"
            :key="tag"
          >{{ tag }}</span>
        </div>
      </div>
    </div>
    <div class="task-card__meta">
      <StatusQuickEdit
        v-if="!board"
        :status="task.status"
        :title="task.title"
        :disabled="moving"
        @change="emit('move', task, $event)"
      />
      <StatusBadge :value="task.priority" />
      <span class="due-date"><CalendarDays :size="15" />{{ formatDate(task.due_date) }}</span>
    </div>
    <div class="task-card__actions">
      <button
        type="button"
        aria-label="Editar tarefa"
        :disabled="moving"
        @click="emit('edit', task)"
      >
        <Pencil :size="16" />
      </button>
      <button
        type="button"
        aria-label="Excluir tarefa"
        :disabled="moving"
        @click="emit('remove', task)"
      >
        <Trash2 :size="16" />
      </button>
      <StatusQuickEdit
        v-if="board"
        :status="task.status"
        :title="task.title"
        :disabled="moving"
        @change="emit('move', task, $event)"
      />
    </div>
  </article>
</template>
