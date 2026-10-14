from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.errors import NotFoundError
from app.domain.task import Task
from app.domain.task_status import TaskStatus
from app.infrastructure.database.models import TaskModel


def to_task(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        titulo=model.titulo,
        descricao=model.descricao,
        status=TaskStatus(model.status),
        data_criacao=model.data_criacao.replace(tzinfo=UTC),
        user_id=model.user_id,
    )


class SqlAlchemyTaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def _get_model(self, task_id: int, user_id: int) -> TaskModel | None:
        return self.session.scalar(
            select(TaskModel).where(
                TaskModel.id == task_id, TaskModel.user_id == user_id
            )
        )

    def get(self, task_id: int, user_id: int) -> Task | None:
        model = self._get_model(task_id, user_id)
        return to_task(model) if model else None

    def list(
        self, user_id: int, status: TaskStatus | None, q: str | None
    ) -> list[Task]:
        statement = select(TaskModel).where(TaskModel.user_id == user_id)
        if status is not None:
            statement = statement.where(TaskModel.status == status.value)
        if q is not None:
            statement = statement.where(TaskModel.titulo.icontains(q, autoescape=True))
        return [
            to_task(model)
            for model in self.session.scalars(
                statement.order_by(TaskModel.data_criacao.desc(), TaskModel.id.desc())
            )
        ]

    def create(
        self, user_id: int, titulo: str, descricao: str, status: TaskStatus
    ) -> Task:
        model = TaskModel(
            user_id=user_id, titulo=titulo, descricao=descricao, status=status.value
        )
        self.session.add(model)
        self.session.flush()
        return to_task(model)

    def update(self, task_id: int, user_id: int, changes: dict) -> Task:
        model = self._get_model(task_id, user_id)
        if model is None:
            raise NotFoundError("Tarefa não encontrada")
        for key, value in changes.items():
            setattr(model, key, value.value if isinstance(value, TaskStatus) else value)
        self.session.flush()
        return to_task(model)

    def delete(self, task_id: int, user_id: int) -> None:
        model = self._get_model(task_id, user_id)
        if model is None:
            raise NotFoundError("Tarefa não encontrada")
        self.session.delete(model)
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
