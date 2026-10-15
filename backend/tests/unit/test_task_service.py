from unittest.mock import Mock

import pytest

from app.application.tasks import TaskService
from app.domain.errors import NotFoundError
from app.domain.task_status import TaskStatus


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_task_prevents_mutation(operation):
    repository = Mock()
    repository.get.return_value = None
    service = TaskService(repository)
    with pytest.raises(NotFoundError):
        if operation == "update":
            service.update(42, 7, {"titulo": "Novo"})
        else:
            getattr(service, operation)(42, 7)
    repository.get.assert_called_once_with(42, 7)
    repository.commit.assert_not_called()
    repository.update.assert_not_called()
    repository.delete.assert_not_called()


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
def test_failed_write_rolls_back_and_propagates(operation):
    repository = Mock()
    repository.commit.side_effect = RuntimeError("Banco indisponível")
    service = TaskService(repository)
    with pytest.raises(RuntimeError, match="Banco indisponível"):
        if operation == "create":
            service.create(7, "Título", "", TaskStatus.BACKLOG)
        elif operation == "update":
            service.update(42, 7, {"titulo": "Novo"})
        else:
            service.delete(42, 7)
    repository.rollback.assert_called_once()


@pytest.mark.parametrize(
    "before,after,has_completion",
    [
        (TaskStatus.BACKLOG, TaskStatus.DONE, True),
        (TaskStatus.DONE, TaskStatus.IN_PROGRESS, False),
    ],
)
def test_completion_timestamp_tracks_status_transition(before, after, has_completion):
    repository = Mock()
    repository.get.return_value.status = before
    TaskService(repository).update(42, 7, {"status": after})
    changes = repository.update.call_args.args[2]
    assert (changes["completed_at"] is not None) is has_completion


def test_editing_completed_task_preserves_completion_timestamp():
    repository = Mock()
    repository.get.return_value.status = TaskStatus.DONE
    TaskService(repository).update(42, 7, {"status": TaskStatus.DONE, "titulo": "Novo"})
    assert "completed_at" not in repository.update.call_args.args[2]
