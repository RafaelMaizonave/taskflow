from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.domain.errors import DomainError
from app.infrastructure.config import Settings
from app.infrastructure.database.session import Database
from app.presentation.auth import router as auth_router
from app.presentation.errors import domain_error_handler, validation_error_handler
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
    app.state.settings = configuration
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuration.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    return app
