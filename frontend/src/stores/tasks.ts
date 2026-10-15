import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { tasksApi } from '../api/tasks'
import { errorMessage } from '../api/client'
import type {
  DashboardSummary,
  Task,
  TaskInput,
  TaskPriority,
  TaskStatus,
} from '../types'
export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref('')
  const loaded = ref(false)
  let generation = 0
  const search = ref('')
  const status = ref<TaskStatus | 'all'>('all')
  const priority = ref<TaskPriority | 'all'>('all')
  const view = ref<'table' | 'board'>('table')
  const filteredTasks = computed(() =>
    tasks.value
      .filter((task) => {
        const term = search.value.trim().toLocaleLowerCase('pt-BR')
        return (
          (!term ||
            [task.title, task.description || '', ...task.tags].some((value) =>
              value.toLocaleLowerCase('pt-BR').includes(term),
            )) &&
          (status.value === 'all' || task.status === status.value) &&
          (priority.value === 'all' || task.priority === priority.value)
        )
      })
      .sort((a, b) => a.position - b.position || b.id - a.id),
  )
  const summary = computed<DashboardSummary>(() => {
    const done = tasks.value.filter((task) => task.status === 'done').length
    return {
      total: tasks.value.length,
      backlog: tasks.value.filter((task) => task.status === 'backlog').length,
      in_progress: tasks.value.filter((task) => task.status === 'in_progress')
        .length,
      done,
      overdue: tasks.value.filter(
        (task) =>
          task.status !== 'done' &&
          task.due_date &&
          task.due_date < localDate(),
      ).length,
      completion_rate: tasks.value.length
        ? Math.round((done / tasks.value.length) * 100)
        : 0,
      upcoming: tasks.value
        .filter((task) => task.status !== 'done' && task.due_date)
        .sort((a, b) => a.due_date!.localeCompare(b.due_date!))
        .slice(0, 4),
    }
  })
  function reset() {
    generation++
    tasks.value = []
    loaded.value = false
    loading.value = false
    search.value = ''
    status.value = 'all'
    priority.value = 'all'
    error.value = ''
    view.value = 'table'
  }
  async function load(force = false) {
    if (loading.value || (loaded.value && !force)) return
    const current = generation
    loading.value = true
    error.value = ''
    try {
      const result = await tasksApi.list()
      if (current === generation) {
        tasks.value = result
        loaded.value = true
      }
    } catch (cause) {
      if (current === generation) error.value = errorMessage(cause)
    } finally {
      if (current === generation) loading.value = false
    }
  }
  async function create(input: TaskInput) {
    const current = generation
    const task = await tasksApi.create(input)
    if (current === generation) tasks.value.unshift(task)
    return task
  }
  async function update(
    id: number,
    input: Partial<TaskInput> & { position?: number },
  ) {
    const current = generation
    const result = await tasksApi.update(id, input)
    if (current === generation)
      tasks.value = tasks.value.map((task) => (task.id === id ? result : task))
  }
  async function remove(id: number) {
    const current = generation
    await tasksApi.remove(id)
    if (current === generation)
      tasks.value = tasks.value.filter((task) => task.id !== id)
  }
  async function move(
    id: number,
    nextStatus: TaskStatus,
    position = tasks.value.filter((task) => task.status === nextStatus).length,
  ) {
    const moving = tasks.value.find((task) => task.id === id)
    if (!moving) return
    const target = tasks.value
      .filter((task) => task.status === nextStatus && task.id !== id)
      .sort((a, b) => a.position - b.position || b.id - a.id)
    target.splice(Math.min(position, target.length), 0, moving)
    try {
      await update(id, {
        status: nextStatus,
        position: target.findIndex((task) => task.id === id),
      })
      for (const [index, task] of target.entries())
        if (task.id !== id && task.position !== index)
          await update(task.id, { position: index })
    } catch (cause) {
      await load(true)
      throw cause
    }
  }
  function setView(value: 'table' | 'board') {
    view.value = value
  }
  return {
    tasks,
    loading,
    error,
    search,
    status,
    priority,
    view,
    filteredTasks,
    summary,
    reset,
    load,
    create,
    update,
    remove,
    move,
    setView,
  }
})
