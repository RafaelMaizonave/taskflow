from dataclasses import dataclass
from datetime import datetime

from app.domain.task_status import TaskStatus


@dataclass(frozen=True)
class Task:
    id: int
    titulo: str
    descricao: str
    status: TaskStatus
    data_criacao: datetime
    user_id: int
