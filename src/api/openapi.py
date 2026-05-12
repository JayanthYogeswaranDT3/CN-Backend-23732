from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


# PUBLIC_INTERFACE
def build_openapi(app: FastAPI) -> dict:
    """Build OpenAPI schema with consistent metadata and tags."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    schema.setdefault("info", {}).setdefault("x-service", "career-navigator-backend")
    app.openapi_schema = schema
    return schema
