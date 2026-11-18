from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self, base, engine: Engine, session_factory: sessionmaker) -> None:
        self._base = base
        self._engine = engine
        self.session_factory = session_factory

    def create_schema(self) -> None:
        self._base.metadata.create_all(bind=self._engine)

    def dispose(self) -> None:
        self._engine.dispose()
