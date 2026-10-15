from datetime import date, datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.domain.task_status import TaskPriority, TaskStatus

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[str, StringConstraints(max_length=10000)]
Tag = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
]
Tags = Annotated[list[Tag], Field(max_length=10)]
Position = Annotated[int, Field(ge=0, le=2**31 - 1, strict=True)]


class TaskFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("tags", check_fields=False)
    @classmethod
    def unique_tags(cls, value):
        return list(dict.fromkeys(value)) if value is not None else value


class CreateTask(TaskFields):
    titulo: Title
    descricao: Description = ""
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None
    tags: Tags = Field(default_factory=list)
    position: Position | None = None


class UpdateTask(TaskFields):
    titulo: Title | None = None
    descricao: Description | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    tags: Tags | None = None
    position: Position | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar")
        if any(
            getattr(self, field) is None
            for field in self.model_fields_set - {"due_date"}
        ):
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
    priority: TaskPriority
    due_date: date | None
    tags: list[str]
    position: int
    updated_at: datetime
    completed_at: datetime | None
