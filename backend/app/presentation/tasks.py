from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.application.tasks import TaskService
from app.domain.task_status import TaskStatus
from app.domain.user import User
from app.infrastructure.database.task_repository import SqlAlchemyTaskRepository
from app.presentation.auth_dependencies import get_current_user
from app.presentation.dependencies import get_session
from app.presentation.task_schemas import CreateTask, TaskResponse, UpdateTask

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
TaskId = Annotated[int, Path(ge=1, le=2**63 - 1)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_task_service(session: Annotated[Session, Depends(get_session)]) -> TaskService:
    return TaskService(SqlAlchemyTaskRepository(session))


Service = Annotated[TaskService, Depends(get_task_service)]


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(payload: CreateTask, user: CurrentUser, service: Service):
    return service.create(user.id, payload.titulo, payload.descricao, payload.status)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    user: CurrentUser,
    service: Service,
    status: TaskStatus | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
):
    return service.list(user.id, status, q)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: TaskId, user: CurrentUser, service: Service):
    return service.get(task_id, user.id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: TaskId, payload: UpdateTask, user: CurrentUser, service: Service
):
    return service.update(task_id, user.id, payload.model_dump(exclude_unset=True))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: TaskId, user: CurrentUser, service: Service) -> Response:
    service.delete(task_id, user.id)
    return Response(status_code=204)
