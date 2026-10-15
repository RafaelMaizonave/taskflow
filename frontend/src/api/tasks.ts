import { api } from './client'
import type { Task, TaskInput } from '../types'
interface ApiTask extends Omit<Task, 'title' | 'description' | 'created_at'> {
  titulo: string
  descricao: string
  data_criacao: string
}
const mapTask = ({
  titulo,
  descricao,
  data_criacao,
  ...task
}: ApiTask): Task => ({
  ...task,
  title: titulo,
  description: descricao,
  created_at: data_criacao,
})
function payload(input: Partial<TaskInput> & { position?: number }) {
  const { title, description, ...rest } = input
  return {
    ...rest,
    ...(title !== undefined ? { titulo: title } : {}),
    ...(description !== undefined ? { descricao: description || '' } : {}),
  }
}
export const tasksApi = {
  async list() {
    return (await api.get<ApiTask[]>('/tasks')).data.map(mapTask)
  },
  async create(input: TaskInput) {
    return mapTask((await api.post<ApiTask>('/tasks', payload(input))).data)
  },
  async update(id: number, input: Partial<TaskInput> & { position?: number }) {
    return mapTask(
      (await api.patch<ApiTask>(`/tasks/${id}`, payload(input))).data,
    )
  },
  async remove(id: number) {
    await api.delete(`/tasks/${id}`)
  },
}
