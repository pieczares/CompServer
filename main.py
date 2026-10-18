import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# from api.results import router as results_router
from db.session import Base, engine
from scheduler import create_scheduler


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    scheduler = create_scheduler()
    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown(wait=True)
        engine.dispose()


app = FastAPI(
    title="Serwer zadań cyklicznych",
    lifespan=lifespan,
)

# app.include_router(results_router)


@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )