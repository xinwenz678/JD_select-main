from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.api import jobs, matches, resumes, suggestions
from app.api.records import router as records_router
from app.core.config import Settings
from app.core.database import build_engine, get_session, init_database
from app.core.errors import ErrorResponse, install_error_handlers


def create_app(config: Settings | None = None) -> FastAPI:
    config = config if config is not None else Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = build_engine(config.database_url)
        application.state.engine = engine
        application.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            init_database(engine)
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title=config.app_name, version="0.1.0", lifespan=lifespan,
        responses={code: {"model": ErrorResponse} for code in (404, 405, 422, 500, 503)},
    )
    application.state.settings = config
    install_error_handlers(application)
    # Added last so CORS also covers normalized error responses.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(records_router)
    application.include_router(resumes.router)
    application.include_router(jobs.router)
    application.include_router(matches.router)
    application.include_router(suggestions.router)

    @application.get("/api/health", tags=["platform"])
    def health(session: Session = Depends(get_session)) -> dict[str, str]:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "version": application.version, "app": config.app_name, "database": "ok"}

    return application


app = create_app()

