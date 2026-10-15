from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database.migrations import migrate


class Database:
    def __init__(self, url: str) -> None:
        database = make_url(url).database
        memory = database == ":memory:"
        self.path = None if memory else Path(database).expanduser().resolve()
        if self.path is not None:
            url = str(make_url(url).set(database=str(self.path)))
        options = {"poolclass": StaticPool} if memory else {}
        self.engine: Engine = create_engine(
            url, connect_args={"check_same_thread": False, "timeout": 10}, **options
        )
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    @staticmethod
    def _enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def initialize(self) -> None:
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        migrate(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def session(self) -> Session:
        return self.sessions()
