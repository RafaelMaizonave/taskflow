import { api } from './client'
import type { Task, TaskInput, TaskStatus } from '../types'

export const tasksApi = {
  async list(params: { q?: string; status?: TaskStatus }, signal?: AbortSignal) {
    return (await api.get<Task[]>('/tasks', { params, signal })).data
  },
  async create(data: TaskInput) { return (await api.post<Task>('/tasks', data)).data },
  async update(id: number, data: Partial<TaskInput>) {
    return (await api.patch<Task>(`/tasks/${id}`, data)).data
  },
  async remove(id: number) { await api.delete(`/tasks/${id}`) },
}
