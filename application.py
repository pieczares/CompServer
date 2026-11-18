import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from core.container import Container
from core.database import Database
from core.settings import Settings
from db.session import Base, SessionLocal, engine


class Application:
    def __init__(self, settings: Settings | None = None) -> None:
        logging.basicConfig(level=logging.INFO)
        self.settings = settings or Settings()
        self.container = Container(
            self.settings, Database(Base, engine, SessionLocal))
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        app = FastAPI(title=self.settings.app_title, lifespan=self._lifespan)
        for controller in self.container.controllers:
            app.include_router(controller.router)
        return app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        self.container.database.create_schema()
        self.container.scheduler.start()
        try:
            yield
        finally:
            self.container.scheduler.shutdown()
            self.container.database.dispose()

    def run(self) -> None:
        uvicorn.run(self.app, host=self.settings.host, port=self.settings.port)
