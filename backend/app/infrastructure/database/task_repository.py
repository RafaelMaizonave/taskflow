from datetime import UTC, datetime
from typing import Unpack

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.application.task_contracts import TaskDetails
from app.domain.errors import NotFoundError
from app.domain.task import Task
from app.domain.task_status import TaskPriority, TaskStatus
from app.infrastructure.database.models import TaskModel


def to_task(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        titulo=model.titulo,
        descricao=model.descricao,
        status=TaskStatus(model.status),
        data_criacao=model.data_criacao.replace(tzinfo=UTC),
        user_id=model.user_id,
        priority=TaskPriority(model.priority),
        due_date=model.due_date,
        tags=tuple(model.tags),
        position=model.position,
        updated_at=model.updated_at.replace(tzinfo=UTC),
        completed_at=(
            model.completed_at.replace(tzinfo=UTC) if model.completed_at else None
        ),
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
            statement = statement.where(
                or_(
                    TaskModel.titulo.icontains(q, autoescape=True),
                    TaskModel.descricao.icontains(q, autoescape=True),
                )
            )
        return [
            to_task(model)
            for model in self.session.scalars(
                statement.order_by(TaskModel.position, TaskModel.id.desc())
            )
        ]

    def create(
        self,
        user_id: int,
        titulo: str,
        descricao: str,
        status: TaskStatus,
        **details: Unpack[TaskDetails],
    ) -> Task:
        if "position" not in details:
            maximum = self.session.scalar(
                select(func.max(TaskModel.position)).where(
                    TaskModel.user_id == user_id, TaskModel.status == status.value
                )
            )
            details["position"] = (maximum if maximum is not None else -1) + 1
        model = TaskModel(
            user_id=user_id,
            titulo=titulo,
            descricao=descricao,
            status=status.value,
            **details,
        )
        self.session.add(model)
        self.session.flush()
        return to_task(model)

    def update(self, task_id: int, user_id: int, changes: dict) -> Task:
        model = self._get_model(task_id, user_id)
        if model is None:
            raise NotFoundError("Tarefa não encontrada")
        model.updated_at = datetime.now(UTC)
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
