<script setup lang="ts">
import axios from 'axios'
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { tasksApi } from '../api/tasks'
import { errorMessage } from '../api/client'
import { useAuthStore } from '../stores/auth'
import TaskEditor from '../components/TaskEditor.vue'
import { statusLabels, type Task, type TaskInput, type TaskStatus } from '../types'

const auth = useAuthStore()
const router = useRouter()
const tasks = ref<Task[]>([])
const query = ref('')
const status = ref<TaskStatus | ''>('')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const notice = ref('')
const editing = ref<Task | null>(null)
const editorOpen = ref(false)
let request: AbortController | undefined

async function load() {
  request?.abort()
  const current = new AbortController()
  request = current
  loading.value = true
  error.value = ''
  try {
    const result = await tasksApi.list({ q: query.value || undefined, status: status.value || undefined }, current.signal)
    if (!current.signal.aborted) tasks.value = result
  } catch (cause) {
    if (!axios.isCancel(cause)) error.value = errorMessage(cause)
  } finally { if (request === current) loading.value = false }
}
onMounted(load)
onUnmounted(() => request?.abort())

function openEditor(task: Task | null = null) {
  editing.value = task
  editorOpen.value = true
  error.value = ''; notice.value = ''
}
async function save(data: TaskInput) {
  if (saving.value) return
  saving.value = true; error.value = ''; notice.value = ''
  try {
    if (editing.value) await tasksApi.update(editing.value.id, data)
    else await tasksApi.create(data)
    editorOpen.value = false
    await load()
    notice.value = 'Tarefa salva com sucesso.'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { saving.value = false }
}
async function changeStatus(task: Task, event: Event) {
  const input = event.target as HTMLSelectElement
  if (saving.value) { input.value = task.status; return }
  saving.value = true; error.value = ''; notice.value = ''
  try {
    await tasksApi.update(task.id, { status: input.value as TaskStatus })
    await load()
    notice.value = 'Status atualizado.'
  } catch (cause) { input.value = task.status; error.value = errorMessage(cause) }
  finally { saving.value = false }
}
async function remove(task: Task) {
  if (saving.value || !window.confirm(`Excluir a tarefa “${task.titulo}”? Esta ação não pode ser desfeita.`)) return
  saving.value = true; error.value = ''; notice.value = ''
  try {
    await tasksApi.remove(task.id)
    if (editing.value?.id === task.id) editorOpen.value = false
    await load()
    notice.value = 'Tarefa excluída.'
  } catch (cause) { error.value = errorMessage(cause) }
  finally { saving.value = false }
}
function logout() { auth.logout(); void router.push('/login') }
function dateLabel(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium' }).format(new Date(value))
}
</script>

<template>
  <div class="workspace">
    <header class="topbar">
      <RouterLink
        class="brand"
        to="/tarefas"
      >
        ◈ <span>TaskFlow</span>
      </RouterLink>
      <div class="account">
        <span>{{ auth.user?.email }}</span>
        <button
          class="button secondary"
          @click="logout"
        >
          Sair
        </button>
      </div>
    </header>
    <main class="dashboard">
      <div class="page-heading">
        <div>
          <span class="eyebrow">SEU ESPAÇO DE FOCO</span><h1>Minhas tarefas<span class="heading-dot">.</span></h1><p class="muted">
            Dê clareza ao seu dia, um passo de cada vez.
          </p>
        </div>
        <button
          class="button primary"
          :disabled="saving"
          @click="openEditor()"
        >
          <span aria-hidden="true">＋</span> Nova tarefa
        </button>
      </div>
      <p
        v-if="error"
        class="notice error"
        role="alert"
      >
        {{ error }}
      </p>
      <p
        v-if="notice"
        class="notice success"
        role="status"
      >
        {{ notice }}
      </p>
      <TaskEditor
        v-if="editorOpen"
        :key="editing?.id || 'new'"
        :task="editing"
        :busy="saving"
        @save="save"
        @cancel="editorOpen = false"
      />
      <form
        class="filters card"
        aria-label="Filtrar tarefas"
        @submit.prevent="load"
      >
        <div class="field search">
          <label for="query">Pesquisar por título</label><input
            id="query"
            v-model="query"
            type="search"
            maxlength="200"
            placeholder="Encontre uma tarefa…"
          >
        </div>
        <div class="field">
          <label for="filter-status">Filtrar por status</label><select
            id="filter-status"
            v-model="status"
          >
            <option value="">
              Todos os status
            </option><option
              v-for="(label, value) in statusLabels"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </select>
        </div>
        <button
          class="button secondary"
          type="submit"
          :disabled="saving"
        >
          Aplicar filtros
        </button>
      </form>
      <div class="list-heading">
        <h2>Suas tarefas</h2><span
          v-if="!loading"
          class="count"
        >{{ tasks.length }} {{ tasks.length === 1 ? 'tarefa' : 'tarefas' }}</span>
      </div>
      <div
        v-if="loading"
        class="empty card"
        role="status"
      >
        Carregando suas tarefas…
      </div>
      <div
        v-else-if="error"
        class="empty card"
      >
        <p>Não foi possível carregar ou atualizar suas tarefas.</p><button
          class="button secondary"
          @click="load"
        >
          Tentar novamente
        </button>
      </div>
      <div
        v-else-if="!tasks.length"
        class="empty card"
      >
        <span
          class="empty-icon"
          aria-hidden="true"
        >✓</span><h3>Nenhuma tarefa por aqui</h3><p class="muted">
          Crie uma tarefa ou ajuste os filtros para começar.
        </p>
      </div>
      <ul
        v-else
        class="task-list"
      >
        <li
          v-for="task in tasks"
          :key="task.id"
          class="task card"
          :class="{ completed: task.status === 'completed' }"
        >
          <div class="task-main">
            <span
              class="badge"
              :class="task.status"
            >{{ statusLabels[task.status] }}</span><h3>{{ task.titulo }}</h3><p
              v-if="task.descricao"
              class="task-description"
            >
              {{ task.descricao }}
            </p><span class="task-date">Criada em {{ dateLabel(task.data_criacao) }}</span>
          </div>
          <div class="task-actions">
            <label
              class="sr-only"
              :for="`status-${task.id}`"
            >Status de {{ task.titulo }}</label><select
              :id="`status-${task.id}`"
              :value="task.status"
              :disabled="saving"
              @change="changeStatus(task, $event)"
            >
              <option
                v-for="(label, value) in statusLabels"
                :key="value"
                :value="value"
              >
                {{ label }}
              </option>
            </select><button
              class="text-button"
              :disabled="saving"
              :aria-label="`Editar ${task.titulo}`"
              @click="openEditor(task)"
            >
              Editar
            </button><button
              class="text-button danger"
              :disabled="saving"
              :aria-label="`Excluir ${task.titulo}`"
              @click="remove(task)"
            >
              Excluir
            </button>
          </div>
        </li>
      </ul>
    </main>
    <footer class="workspace-footer">
      TaskFlow · Espaço para o que importa.
    </footer>
  </div>
</template>
