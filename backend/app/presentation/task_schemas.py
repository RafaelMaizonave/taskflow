from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.domain.task_status import TaskStatus

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[str, StringConstraints(max_length=10000)]


class CreateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: Title
    descricao: Description = ""
    status: TaskStatus = TaskStatus.PENDING


class UpdateTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: Title | None = None
    descricao: Description | None = None
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Os campos informados não podem ser nulos")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    descricao: str
    status: TaskStatus
    data_criacao: datetime
    user_id: int
