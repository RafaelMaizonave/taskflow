from app.application.task_contracts import TaskRepository
from app.domain.errors import NotFoundError
from app.domain.task import Task
from app.domain.task_status import TaskStatus


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def get(self, task_id: int, user_id: int) -> Task:
        task = self.repository.get(task_id, user_id)
        if task is None:
            raise NotFoundError("Tarefa não encontrada")
        return task

    def list(
        self, user_id: int, status: TaskStatus | None, q: str | None
    ) -> list[Task]:
        return self.repository.list(user_id, status, q)

    def create(
        self, user_id: int, titulo: str, descricao: str, status: TaskStatus
    ) -> Task:
        try:
            task = self.repository.create(user_id, titulo, descricao, status)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
        return task

    def update(self, task_id: int, user_id: int, changes: dict) -> Task:
        self.get(task_id, user_id)
        try:
            task = self.repository.update(task_id, user_id, changes)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
        return task

    def delete(self, task_id: int, user_id: int) -> None:
        self.get(task_id, user_id)
        try:
            self.repository.delete(task_id, user_id)
            self.repository.commit()
        except Exception:
            self.repository.rollback()
            raise
