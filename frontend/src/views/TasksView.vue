<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Columns3,
  Filter,
  LayoutList,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Sparkles,
} from '@lucide/vue'
import BaseButton from '../components/ui/BaseButton.vue'
import SelectMenu from '../components/ui/SelectMenu.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskFormDrawer from '../components/tasks/TaskFormDrawer.vue'
import { LIMITS } from '../constants/limits'
import { useTasksStore } from '../stores/tasks'
import { useToasts } from '../composables/useToasts'
import type { Task, TaskStatus, TaskPriority } from '../types'

const tasks = useTasksStore()
const { show } = useToasts()
const drawerOpen = ref(false)
const selectedTask = ref<Task | null>(null)
const dragged = ref<Task | null>(null)
const movingIds = ref(new Set<number>())

const columns: { status: TaskStatus; label: string; tone: string }[] = [
  { status: 'backlog', label: 'Backlog', tone: 'violet' },
  { status: 'in_progress', label: 'Em andamento', tone: 'blue' },
  { status: 'done', label: 'Concluídas', tone: 'green' },
]
const statusOptions = [
  { value: 'all', label: 'Todos os status' },
  { value: 'backlog', label: 'Backlog', tone: 'backlog' },
  { value: 'in_progress', label: 'Em andamento', tone: 'in_progress' },
  { value: 'done', label: 'Concluídas', tone: 'done' },
]
const priorityOptions = [
  { value: 'all', label: 'Todas as prioridades' },
  { value: 'high', label: 'Alta', tone: 'high' },
  { value: 'medium', label: 'Média', tone: 'medium' },
  { value: 'low', label: 'Baixa', tone: 'low' },
]
const grouped = computed(() =>
  Object.fromEntries(
    columns.map((column) => [
      column.status,
      tasks.filteredTasks.filter((task) => task.status === column.status),
    ]),
  ),
)
const hasFilters = computed(
  () => tasks.search || tasks.status !== 'all' || tasks.priority !== 'all',
)

function createTask() {
  selectedTask.value = null
  drawerOpen.value = true
}
function editTask(task: Task) {
  selectedTask.value = task
  drawerOpen.value = true
}
async function removeTask(task: Task) {
  if (
    !window.confirm(`Excluir “${task.title}”? Esta ação não pode ser desfeita.`)
  )
    return
  try {
    await tasks.remove(task.id)
    show('Tarefa excluída.')
  } catch {
    show('Não foi possível excluir a tarefa.', 'error')
  }
}
async function moveTask(task: Task, status: TaskStatus, position?: number) {
  if (movingIds.value.has(task.id)) return
  movingIds.value.add(task.id)
  try {
    if (position === undefined) {
      const lastPosition = tasks.tasks.reduce((last, item) =>
        item.id !== task.id && item.status === status ? Math.max(last, item.position) : last, -1)
      await tasks.update(task.id, { status, position: lastPosition + 1 })
    } else {
      await tasks.move(task.id, status, position)
    }
    show(status === 'done' ? 'Tarefa concluída.' : 'Tarefa movida.')
  } catch {
    show('Não foi possível mover a tarefa.', 'error')
  } finally {
    movingIds.value.delete(task.id)
  }
}
async function drop(status: TaskStatus, position?: number) {
  if (!dragged.value) return
  const task = dragged.value
  dragged.value = null
  await moveTask(task, status, position)
}
function clearFilters() {
  tasks.search = ''
  tasks.status = 'all'
  tasks.priority = 'all'
}

onMounted(() => tasks.load())
</script>

<template>
  <div class="tasks-page">
    <header class="page-header">
      <div>
        <h1>Minhas tarefas</h1>
      </div>
      <BaseButton @click="createTask">
        <Plus :size="18" /> Nova tarefa
      </BaseButton>
    </header>

    <section class="task-toolbar">
      <label class="task-search">
        <Search :size="18" />
        <input
          v-model="tasks.search"
          aria-label="Buscar por tarefa ou tag"
          placeholder="Buscar por tarefa ou tag..."
          :maxlength="LIMITS.SEARCH"
        >
      </label>
      <SelectMenu
        :model-value="tasks.status"
        label="Filtrar por status"
        :options="statusOptions"
        variant="filter"
        @update:model-value="tasks.status = $event as TaskStatus | 'all'"
      >
        <template #icon>
          <Filter :size="17" />
        </template>
      </SelectMenu>
      <SelectMenu
        :model-value="tasks.priority"
        label="Filtrar por prioridade"
        :options="priorityOptions"
        variant="filter"
        @update:model-value="tasks.priority = $event as TaskPriority | 'all'"
      >
        <template #icon>
          <SlidersHorizontal :size="17" />
        </template>
      </SelectMenu>
      <button
        v-if="hasFilters"
        class="clear-filter"
        type="button"
        @click="clearFilters"
      >
        <RotateCcw :size="15" /> Limpar
      </button>
      <div
        class="view-switch"
        aria-label="Tipo de visualização"
      >
        <button
          type="button"
          :class="{ active: tasks.view === 'table' }"
          aria-label="Visualização em lista"
          @click="tasks.setView('table')"
        >
          <LayoutList :size="18" />
        </button>
        <button
          type="button"
          :class="{ active: tasks.view === 'board' }"
          aria-label="Visualização em quadro"
          @click="tasks.setView('board')"
        >
          <Columns3 :size="18" />
        </button>
      </div>
    </section>

    <div class="task-results-info">
      <span><strong>{{ tasks.filteredTasks.length }}</strong>
        {{ tasks.filteredTasks.length === 1 ? 'tarefa' : 'tarefas' }}</span>
      <span v-if="tasks.view === 'board'"><Sparkles :size="15" /> Arraste os cards para atualizar o status</span>
    </div>

    <section
      v-if="tasks.loading"
      class="tasks-loading"
    >
      <i
        v-for="n in 5"
        :key="n"
      />
    </section>
    <section
      v-else-if="!tasks.filteredTasks.length"
      class="empty-state"
    >
      <div class="empty-state__art">
        <span /><span /><span />
        <svg
          viewBox="0 0 48 48"
          aria-hidden="true"
        >
          <path d="m13 24 7 7 15-16" />
        </svg>
      </div>
      <h2>
        {{
          hasFilters ? 'Nenhum resultado encontrado' : 'Seu fluxo começa aqui'
        }}
      </h2>
      <p>
        {{
          hasFilters
            ? 'Tente ajustar ou limpar os filtros usados.'
            : 'Crie a primeira tarefa e dê forma ao seu dia.'
        }}
      </p>
      <BaseButton
        v-if="hasFilters"
        variant="secondary"
        @click="clearFilters"
      >
        Limpar filtros
      </BaseButton>
      <BaseButton
        v-else
        @click="createTask"
      >
        <Plus :size="18" /> Criar primeira tarefa
      </BaseButton>
    </section>

    <section
      v-else-if="tasks.view === 'table'"
      class="task-table"
    >
      <div class="task-table__head">
        <span>Tarefa</span><span>Status</span><span>Prioridade</span><span>Prazo</span><span>Ações</span>
      </div>
      <TaskCard
        v-for="task in tasks.filteredTasks"
        :key="task.id"
        :task="task"
        :moving="movingIds.has(task.id)"
        @edit="editTask"
        @remove="removeTask"
        @move="moveTask"
      />
    </section>

    <section
      v-else
      class="kanban"
    >
      <div
        v-for="column in columns"
        :key="column.status"
        class="kanban-column"
        @dragover.prevent
        @drop="drop(column.status)"
      >
        <header>
          <div>
            <i :class="`dot--${column.tone}`" /><strong>{{
              column.label
            }}</strong><span>{{ grouped[column.status]?.length }}</span>
          </div>
          <button
            type="button"
            aria-label="Adicionar tarefa"
            @click="createTask"
          >
            <Plus :size="17" />
          </button>
        </header>
        <div class="kanban-column__body">
          <TaskCard
            v-for="task in grouped[column.status] || []"
            :key="task.id"
            :task="task"
            :moving="movingIds.has(task.id)"
            board
            @dragstart="dragged = task"
            @dragover.prevent
            @drop.stop="drop(column.status, task.position)"
            @edit="editTask"
            @remove="removeTask"
            @move="moveTask"
          />
          <button
            class="kanban-add"
            type="button"
            @click="createTask"
          >
            <Plus :size="16" /> Adicionar tarefa
          </button>
        </div>
      </div>
    </section>

    <TaskFormDrawer
      v-model:open="drawerOpen"
      :task="selectedTask"
    />
  </div>
</template>
