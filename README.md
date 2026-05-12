# Career Navigator Backend

Production-grade FastAPI backend scaffold using clean architecture with:
- Python **>= 3.11**
- FastAPI **>= 0.110**
- Pydantic **>= 2**
- SQLAlchemy **>= 2**
- PostgreSQL **>= 15**

This repository is a scaffold intended to be extended into the Career Navigator backend. It includes:
- Clean modular architecture separation (API / service / repository / models / schemas)
- Structured logging
- Centralized settings (Pydantic Settings)
- Middleware for request id / timing / security headers
- Database session management (SQLAlchemy 2.0 async)
- Health checks
- Sample CRUD module (`items`)
- Tests layout
- Dockerfile, docker-compose, Makefile, .env.example
- Alembic migrations scaffold

---

## Quickstart (Docker)

1) Copy env template and fill values:
```bash
cp .env.example .env
```

2) Build and run:
```bash
make up
```

3) Open API docs:
- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health

---

## Quickstart (local without Docker)

Requirements: Python 3.11+ and PostgreSQL 15+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env to point DATABASE_URL to your Postgres instance

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Architecture Overview (Clean / Modular)

The code is organized so that **domain/business logic does not depend on frameworks**.

### Folder responsibilities

- `app/api/`
  - **Purpose:** HTTP API layer (FastAPI routers), request/response handling, dependency wiring for endpoints.
  - **Should contain:** routers, endpoint dependencies, API versioning (`/api/v1`), API-level DTOs if needed.
  - **Should NOT contain:** raw SQL, business rules, cross-cutting infrastructure logic.

- `app/core/`
  - **Purpose:** cross-cutting application core utilities (settings, logging, exceptions, middleware, security helpers).
  - **Should contain:** config, app startup, logging configuration, shared exception types, middleware.
  - **Should NOT contain:** feature-specific business logic.

- `app/db/`
  - **Purpose:** database engine/session factory, base ORM model, migrations integration glue.
  - **Should contain:** async engine, session dependency, base model.
  - **Should NOT contain:** feature repositories (those live under the feature).

- `app/modules/<feature>/`
  - **Purpose:** feature modules (vertical slices). Each feature has:
    - `models` (SQLAlchemy entities)
    - `schemas` (Pydantic DTOs)
    - `repository` (data access)
    - `service` (business logic)
    - `router` (API)
  - **Should NOT contain:** unrelated features.

- `app/background/`
  - **Purpose:** background jobs / scheduled tasks.
  - **Note:** Scaffold placeholder included for later integration with Celery/RQ/Arq.

- `tests/`
  - **Purpose:** unit/integration tests. Async test client + DB isolation patterns.
  - **Note:** Scaffold tests are minimal; expand with testcontainers or ephemeral DB in CI.

---

## Request Flow

**HTTP request -> FastAPI router -> service -> repository -> database**

Example for `items` CRUD:
1. Router validates request via Pydantic schema
2. Router calls `ItemService`
3. Service enforces business rules and orchestrates work
4. Repository performs SQLAlchemy async operations
5. Response schema is returned

---

## Dependency Flow (inversion-friendly)

- API layer depends on service interfaces/classes
- Service depends on repository interfaces/classes
- Repository depends on DB session (injected)
- DB engine/session created centrally in `app/db/session.py`
- Settings provided centrally from `app/core/config.py`

---

## Scaling later

- Add more modules under `app/modules/*` without bloating global folders.
- Split routers per module and keep API v1 composition in `app/api/v1/api.py`.
- Add caching (Redis) behind `app/core/cache/` and inject into services.
- Add auth (JWT/OAuth2) in `app/core/security.py` + `app/api/deps.py`.

---

## Microservice extraction readiness

Each `app/modules/<feature>` is a vertical slice. If a module grows large, it can be:
- extracted into its own service (copy module + shared core utilities)
- keep contracts stable via OpenAPI schema and versioned API (`/api/v1`)
- share Pydantic schemas via a separate shared package later (optional)

---
"
