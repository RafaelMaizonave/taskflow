from dataclasses import dataclass
from datetime import date, datetime

from app.domain.task_status import TaskPriority, TaskStatus


@dataclass(frozen=True)
class Task:
    id: int
    titulo: str
    descricao: str
    status: TaskStatus
    data_criacao: datetime
    user_id: int
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    tags: tuple[str, ...] = ()
    position: int = 0
    updated_at: datetime | None = None
    completed_at: datetime | None = None
