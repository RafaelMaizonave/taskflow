from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import Settings
from app.infrastructure.database.session import Database
from app.presentation.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings if settings is not None else Settings()
    database = Database(configuration.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            database.initialize()
            yield
        finally:
            database.close()

    app = FastAPI(title="TaskFlow API", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(health_router)
    return app
