from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors.handlers import install_exception_handlers
from src.api.middleware.logging import AccessLogMiddleware
from src.api.middleware.request_id import RequestIdMiddleware
from src.api.openapi import build_openapi
from src.api.routes.api_v1 import router as api_v1_router
from src.api.routes.health import router as health_router
from src.core.lifecycle import lifespan
from src.core.settings import get_settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured app instance with routes, middleware, exception handlers,
        and OpenAPI metadata.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Career Navigator backend API (clean modular scaffold).",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_tags=[
            {"name": "Health", "description": "Service health and readiness checks."},
            {"name": "Users", "description": "Sample CRUD module (users)."},
        ],
    )

    # OpenAPI customization (keeps docs stable and consistent)
    app.openapi = lambda: build_openapi(app)  # type: ignore[assignment]

    # Middleware: request id -> access logging -> CORS (order matters for logging context)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AccessLogMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Exception handlers
    install_exception_handlers(app)

    # Routes
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
