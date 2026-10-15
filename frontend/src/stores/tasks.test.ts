import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { tasksApi } from '../api/tasks'
import { localDate, useTasksStore } from './tasks'
import type { Task } from '../types'
vi.mock('../api/tasks', () => ({
  tasksApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}))
const task: Task = {
  id: 1,
  title: 'Planejar',
  description: 'Pesquisar clientes',
  tags: ['Produto'],
  status: 'backlog',
  priority: 'high',
  due_date: '2000-01-01',
  position: 0,
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
  completed_at: null,
}
beforeEach(() => {
  setActivePinia(createPinia())
  vi.resetAllMocks()
})
describe('Tarefas reais', () => {
  it('calcula progresso, atraso e busca incluindo descrição e tags', async () => {
    vi.mocked(tasksApi.list).mockResolvedValue([
      task,
      { ...task, id: 2, title: 'Finalizada', status: 'done' },
    ])
    const store = useTasksStore()
    await store.load()
    expect(store.summary.completion_rate).toBe(50)
    expect(store.summary.overdue).toBe(1)
    store.search = 'CLIENTES'
    expect(store.filteredTasks).toHaveLength(2)
    store.priority = 'low'
    expect(store.filteredTasks).toHaveLength(0)
    store.reset()
    expect(store.tasks).toHaveLength(0)
    expect(store.search).toBe('')
  })
  it('descarta respostas de uma conta após encerrar a sessão', async () => {
    let resolve!: (value: Task[]) => void
    vi.mocked(tasksApi.list).mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done
        }),
    )
    const store = useTasksStore()
    const loading = store.load()
    store.reset()
    resolve([task])
    await loading
    expect(store.tasks).toHaveLength(0)
  })
  it('preserva os dados quando uma mudança de status falha', async () => {
    vi.mocked(tasksApi.list).mockResolvedValue([task])
    vi.mocked(tasksApi.update).mockRejectedValue(new Error('Falha'))
    const store = useTasksStore()
    await store.load()
    await expect(store.move(1, 'done')).rejects.toThrow('Falha')
    expect(store.tasks[0]?.status).toBe('backlog')
  })
  it('usa o dia local nos prazos', () => {
    expect(localDate(new Date(2026, 9, 15, 23, 59))).toBe('2026-10-15')
  })
})
