import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.models import TaskModel, UserModel
from app.infrastructure.database.session import Database


@pytest.fixture
def database(settings):
    database = Database(settings.database_url)
    database.initialize()
    yield database
    database.close()


def test_initialization_is_repeatable_and_keeps_data(database):
    with database.session() as session:
        session.add(UserModel(email="user@example.com", password_hash="test-hash"))
        session.commit()
    database.initialize()
    assert set(inspect(database.engine).get_table_names()) == {"users", "tasks"}
    with database.session() as session:
        assert session.scalar(select(func.count()).select_from(UserModel)) == 1


def test_relationship_defaults_and_cascade(database):
    with database.session() as session:
        user = UserModel(email="user@example.com", password_hash="test-hash")
        task = TaskModel(titulo="Primeira tarefa", user=user)
        session.add(user)
        session.commit()
        assert task.status == "pending"
        assert task.descricao == ""
        assert task.data_criacao is not None
        user_id = user.id
    with database.session() as session:
        user = session.get(UserModel, user_id)
        session.delete(user)
        session.commit()
        assert session.scalar(select(func.count()).select_from(TaskModel)) == 0


def test_email_is_unique(database):
    with database.session() as session:
        session.add_all(
            [
                UserModel(email="same@example.com", password_hash="hash"),
                UserModel(email="same@example.com", password_hash="hash"),
            ]
        )
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize(
    "values",
    [
        {"titulo": "", "status": "pending"},
        {"titulo": "  ", "status": "pending"},
        {"titulo": "x" * 201, "status": "pending"},
        {"titulo": "Task", "status": "invalid"},
    ],
)
def test_rejects_invalid_task_values(database, values):
    with database.session() as session:
        user = UserModel(email="user@example.com", password_hash="hash")
        session.add(TaskModel(**values, user=user))
        with pytest.raises(IntegrityError):
            session.commit()


def test_foreign_key_prevents_orphan_task(database):
    with database.session() as session:
        session.add(TaskModel(titulo="Orphan", user_id=999))
        with pytest.raises(IntegrityError):
            session.commit()


def test_session_rolls_back_uncommitted_changes(database):
    with database.session() as session:
        session.add(UserModel(email="rollback@example.com", password_hash="hash"))
        session.flush()
    with database.session() as session:
        assert session.scalar(select(func.count()).select_from(UserModel)) == 0


def test_sessions_are_independent(database):
    with database.session() as first, database.session() as second:
        assert first is not second


def test_data_survives_engine_restart(settings):
    first = Database(settings.database_url)
    first.initialize()
    with first.session() as session:
        session.add(UserModel(email="persist@example.com", password_hash="hash"))
        session.commit()
    first.close()
    second = Database(settings.database_url)
    try:
        second.initialize()
        with second.session() as session:
            assert session.scalar(select(UserModel.email)) == "persist@example.com"
    finally:
        second.close()


@pytest.mark.parametrize("status", ["pending", "in_progress", "completed"])
def test_accepts_supported_status(database, status):
    with database.session() as session:
        user = UserModel(email="status@example.com", password_hash="hash")
        task = TaskModel(titulo="Tarefa", status=status, user=user)
        session.add(task)
        session.commit()
        assert session.get(TaskModel, task.id).status == status
