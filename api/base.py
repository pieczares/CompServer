from abc import ABC

from fastapi import APIRouter


class Controller(ABC):
    def __init__(self, prefix: str = "", tags: list[str] | None = None) -> None:
        self.router = APIRouter(prefix=prefix, tags=tags or [])
