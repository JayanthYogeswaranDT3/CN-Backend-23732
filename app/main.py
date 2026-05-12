from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.api import router as api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import ProcessTimeMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware
from app.db.session import close_engine, init_engine


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings)

    openapi_tags = [
        {"name": "health", "description": "Health and service status endpoints."},
        {"name": "items", "description": "Sample CRUD endpoints for items."},
    ]

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Career Navigator Backend API (scaffold).",
        openapi_tags=openapi_tags,
    )

    # Middleware
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routers
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    @app.on_event("startup")
    async def _startup() -> None:
        """Initialize resources needed by the application."""
        init_engine()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        """Cleanup resources on shutdown."""
        await close_engine()

    return app


app = create_app()
"
