import logging
from abc import ABC, abstractmethod

from sqlalchemy.orm import sessionmaker


class Task(ABC):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self._log = logging.getLogger(type(self).__name__)

    @abstractmethod
    def run(self) -> None:
        ...

    def __call__(self) -> None:
        self.run()
