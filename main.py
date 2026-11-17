import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.produkty import ProduktyController
from db.session import Base, engine, SessionLocal
from scheduler import JobScheduler
from services.product_link_service import ProductLinkService
from services.product_scraper import ProductScraper
from tasks.productlinks import RefreshProductLinksTask
from tasks.produkty import RefreshProductsTask

logging.basicConfig(level=logging.INFO)


class Application:
    def __init__(self) -> None:
        self.scheduler = JobScheduler(
            RefreshProductLinksTask(SessionLocal, ProductLinkService(5, 500)),
            RefreshProductsTask(SessionLocal, ProductScraper(threads=5),
                                links_limit=100),
        )
        self.app = FastAPI(title="Serwer zadań cyklicznych",
                           lifespan=self._lifespan)
        self.app.include_router(ProduktyController().router)
        self.app.add_api_route("/health", self.health, methods=["GET"])

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        Base.metadata.create_all(bind=engine)
        self.scheduler.start()
        try:
            yield
        finally:
            self.scheduler.shutdown()
            engine.dispose()

    @staticmethod
    def health() -> dict:
        return {"status": "ok"}


app = Application().app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
