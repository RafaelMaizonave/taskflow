"""Versioned SQLite schema upgrades preserving existing account and task data."""

from sqlalchemy import Engine

from app.infrastructure.database.models import Base

SCHEMA_VERSION = 2


def migrate(engine: Engine) -> None:
    with engine.connect() as connection:
        version = connection.exec_driver_sql("PRAGMA user_version").scalar_one()
        if version > SCHEMA_VERSION:
            raise RuntimeError("A versão do banco é mais recente que esta aplicação")
        tables = (
            connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            .scalars()
            .all()
        )
        if "tasks" not in tables:
            Base.metadata.create_all(connection)
            connection.exec_driver_sql(f"PRAGMA user_version={SCHEMA_VERSION}")
            connection.commit()
            return
        if version == SCHEMA_VERSION:
            return
        if version == 0:
            columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(tasks)")
            }
            if "priority" in columns:
                raise RuntimeError(
                    "Esquema sem versão reconhecida; migração manual necessária"
                )
            # SQLite cannot replace a CHECK constraint without rebuilding the table.
            connection.commit()
            with connection.begin():
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT ''"
                )
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN created_at DATETIME"
                )
                connection.exec_driver_sql("ALTER TABLE tasks RENAME TO tasks_legacy")
                connection.exec_driver_sql("DROP INDEX IF EXISTS ix_tasks_user_status")
                Base.metadata.tables["tasks"].create(connection)
                connection.exec_driver_sql("""
                    INSERT INTO tasks
                        (id, titulo, descricao, status, data_criacao, user_id,
                         priority, due_date, tags, position, updated_at, completed_at)
                    SELECT id, titulo, descricao,
                        CASE status WHEN 'pending' THEN 'backlog'
                                    WHEN 'completed' THEN 'done' ELSE status END,
                        data_criacao, user_id, 'medium', NULL, '[]',
                        ROW_NUMBER() OVER (
                            PARTITION BY user_id, status
                            ORDER BY data_criacao DESC, id DESC
                        ) - 1,
                        data_criacao, NULL
                    FROM tasks_legacy
                """)
                connection.exec_driver_sql("DROP TABLE tasks_legacy")
                connection.exec_driver_sql("PRAGMA user_version=1")
            version = 1
        if version == 1:
            user_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(users)")
            }
            connection.commit()
            with connection.begin():
                if "token_version" not in user_columns:
                    connection.exec_driver_sql(
                        "ALTER TABLE users ADD COLUMN token_version "
                        "INTEGER NOT NULL DEFAULT 0"
                    )
                connection.exec_driver_sql(f"PRAGMA user_version={SCHEMA_VERSION}")
