export type TaskStatus = 'backlog' | 'in_progress' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface User {
  id: number
  name: string
  email: string
  created_at: string | null
}

export interface Task {
  id: number
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
  tags: string[]
  position: number
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface TaskInput {
  title: string
  description?: string | null
  status: TaskStatus
  priority: TaskPriority
  due_date?: string | null
  tags: string[]
}

export interface DashboardSummary {
  total: number
  backlog: number
  in_progress: number
  done: number
  overdue: number
  completion_rate: number
  upcoming: Task[]
}
