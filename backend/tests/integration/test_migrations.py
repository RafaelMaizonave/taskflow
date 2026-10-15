import sqlite3

from sqlalchemy import select

from app.infrastructure.database.models import TaskModel, UserModel
from app.infrastructure.database.session import Database


def test_legacy_migration_preserves_accounts_tasks_and_unknown_dates(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY,
                                email VARCHAR(254) NOT NULL UNIQUE,
                                password_hash VARCHAR(255) NOT NULL);
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY, titulo VARCHAR(200) NOT NULL,
                descricao TEXT NOT NULL, status VARCHAR(20) NOT NULL,
                data_criacao DATETIME NOT NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT task_status CHECK (
                    status IN ('pending','in_progress','completed'))
            );
            CREATE INDEX ix_tasks_user_status ON tasks(user_id,status);
            INSERT INTO users VALUES (7, 'legacy@example.com', 'original-hash');
            INSERT INTO tasks VALUES
                (11,'Pendente','Texto','pending','2025-01-02 10:00:00',7);
            INSERT INTO tasks VALUES
                (12,'Concluída','','completed','2025-01-03 10:00:00',7);
        """)
    database = Database(f"sqlite:///{path}")
    try:
        database.initialize()
        database.initialize()
        with database.session() as session:
            user = session.get(UserModel, 7)
            assert user.password_hash == "original-hash"
            assert user.created_at is None
            assert user.name == ""
            tasks = session.scalars(select(TaskModel).order_by(TaskModel.id)).all()
            assert [task.id for task in tasks] == [11, 12]
            assert [task.status for task in tasks] == ["backlog", "done"]
            assert tasks[0].descricao == "Texto"
            assert tasks[0].data_criacao.isoformat() == "2025-01-02T10:00:00"
            assert all(task.user_id == 7 and task.tags == [] for task in tasks)
            assert all(task.completed_at is None for task in tasks)
        with database.engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA user_version").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        database.close()


def test_failed_migration_rolls_back_schema_and_data(tmp_path):
    import pytest
    from sqlalchemy.exc import IntegrityError

    path = tmp_path / "invalid-legacy.db"
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT);
            CREATE TABLE tasks (id INTEGER PRIMARY KEY, titulo TEXT, descricao TEXT,
                                status TEXT, data_criacao DATETIME, user_id INTEGER);
            INSERT INTO users VALUES (1, 'user@example.com', 'hash');
            INSERT INTO tasks VALUES
                (1, 'Preservar', '', 'unknown', '2025-01-01 10:00:00', 1);
        """)
    database = Database(f"sqlite:///{path}")
    try:
        with pytest.raises(IntegrityError):
            database.initialize()
        with sqlite3.connect(path) as connection:
            assert connection.execute("SELECT status FROM tasks").fetchone() == (
                "unknown",
            )
            assert "name" not in {
                row[1] for row in connection.execute("PRAGMA table_info(users)")
            }
            assert connection.execute("PRAGMA user_version").fetchone() == (0,)
    finally:
        database.close()
