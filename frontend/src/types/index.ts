export interface User { id: number; email: string }
export type TaskStatus = 'pending' | 'in_progress' | 'completed'
export interface Task {
  id: number
  titulo: string
  descricao: string
  status: TaskStatus
  data_criacao: string
  user_id: number
}
export interface TaskInput { titulo: string; descricao: string; status: TaskStatus }
export const statusLabels: Record<TaskStatus, string> = {
  pending: 'Pendente', in_progress: 'Em andamento', completed: 'Concluída',
}
