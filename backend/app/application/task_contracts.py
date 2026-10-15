from datetime import date, datetime
from typing import Protocol, TypedDict, Unpack

from app.domain.task import Task
from app.domain.task_status import TaskPriority, TaskStatus


class TaskDetails(TypedDict, total=False):
    priority: TaskPriority
    due_date: date | None
    tags: list[str]
    position: int
    completed_at: datetime | None


class TaskRepository(Protocol):
    def get(self, task_id: int, user_id: int) -> Task | None: ...
    def list(
        self, user_id: int, status: TaskStatus | None, q: str | None
    ) -> list[Task]: ...
    def create(
        self,
        user_id: int,
        titulo: str,
        descricao: str,
        status: TaskStatus,
        **details: Unpack[TaskDetails],
    ) -> Task: ...
    def update(self, task_id: int, user_id: int, changes: dict) -> Task: ...
    def delete(self, task_id: int, user_id: int) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
