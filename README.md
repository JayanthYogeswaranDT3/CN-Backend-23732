# Backend (FastAPI) — Production-grade Scaffold (Clean Modular Architecture)

This backend scaffold implements a **clean modular architecture** using:

- Python **>= 3.11**
- FastAPI **>= 0.110** (pinned to `0.115.7` per workspace constraints)
- Pydantic **v2** (pinned to `2.10.6`)
- SQLAlchemy **v2** async (pinned to `2.0.37`)
- PostgreSQL **15** (via docker-compose)
- Async-first request handling, repository + service patterns, dependency injection

## Goals

- Clear separation of concerns (API vs services vs repositories vs persistence)
- Production-friendly defaults:
  - structured logging
  - robust settings management
  - centralized error handling
  - health checks
  - graceful startup/shutdown
  - DB session lifecycle management
  - tests + CI readiness
- Easy to scale:
  - add modules without touching global code
  - support for future extraction into microservices

---

## Folder structure (what each folder is for)

```
backend/
  src/
    api/
      main.py
      deps.py
      routes/
        health.py
        api_v1.py
        v1/
          users.py
      middleware/
        request_id.py
        logging.py
      errors/
        handlers.py
        exceptions.py
      openapi.py
    core/
      settings.py
      logging.py
      lifecycle.py
      security.py
      time.py
    db/
      session.py
      base.py
      init_db.py
    models/
      user.py
    schemas/
      user.py
      common.py
      health.py
    repositories/
      user_repository.py
    services/
      user_service.py
    utils/
      ids.py
      pagination.py
  tests/
    conftest.py
    test_health.py
    test_users.py
  alembic/
    env.py
    script.py.mako
    versions/
  alembic.ini
  Dockerfile
  docker-compose.yml
  Makefile
  pyproject.toml
  requirements.txt
  .env.example
```

### `src/api/` — API layer (FastAPI boundary)
**Purpose**
- Defines HTTP endpoints, request/response models, dependency injection, middleware registration, exception handlers, OpenAPI configuration.

**Responsibilities**
- Validate inputs (via Pydantic)
- Call the service layer
- Translate domain/service errors into HTTP responses
- No DB access directly

**What should NOT go here**
- SQLAlchemy queries
- complex business logic
- data access decisions

### `src/services/` — business logic / orchestration
**Purpose**
- Implements use-cases (e.g., “create user”, “list users”) and orchestrates repositories.

**Responsibilities**
- Business rules, validation beyond schema-level, idempotency decisions, transactional orchestration (in collaboration with the DB session).

**What should NOT go here**
- FastAPI objects (`Request`, `Response`, `APIRouter`)
- raw SQLAlchemy queries (those live in repositories)

### `src/repositories/` — data access (repository pattern)
**Purpose**
- Encapsulates persistence concerns (SQLAlchemy queries) behind a stable interface.

**Responsibilities**
- Query/write the database using SQLAlchemy async Session
- Return ORM models (or domain entities if you later introduce them)

**What should NOT go here**
- HTTP concerns
- cross-aggregate business orchestration (belongs in services)

### `src/models/` — persistence models (SQLAlchemy ORM)
**Purpose**
- SQLAlchemy ORM models describing tables.

**Responsibilities**
- DB schema mapping and constraints

**What should NOT go here**
- Pydantic request/response schemas (those are in `schemas/`)
- API logic

### `src/schemas/` — DTOs (Pydantic v2 models)
**Purpose**
- Input/output contracts for API and service boundaries.

**Responsibilities**
- Request validation, response serialization contracts
- Separate “create/update” schemas from “read” schemas

**What should NOT go here**
- SQLAlchemy models
- database session handling

### `src/core/` — configuration + cross-cutting infrastructure
**Purpose**
- Settings, logging configuration, lifecycle hooks, and security utilities.

**Responsibilities**
- Centralized configuration management (Pydantic Settings)
- App lifecycle orchestration (startup/shutdown)
- Logging format & correlation
- Security helpers (password hashing placeholder, etc.)

**What should NOT go here**
- Feature/business modules (those belong in services/repos/api routes)

### `src/db/` — database session management + base metadata
**Purpose**
- SQLAlchemy engine/session creation, DB initialization.

**Responsibilities**
- Create async engine
- Manage connection pooling
- Provide `get_db_session` dependency
- Provide `Base` registry

**What should NOT go here**
- Application business logic
- HTTP routes

### `src/utils/` — small shared helpers
**Purpose**
- Small stateless helpers used across modules.

**What should NOT go here**
- Anything that creates “hidden coupling” between modules
- business logic

### `alembic/` and `alembic.ini` — migrations
**Purpose**
- Database schema migrations.
- In production, migrations should be executed as a separate step in CI/CD.

---

## Request flow (end-to-end)

1. Incoming request hits FastAPI (`src/api/main.py`)
2. Middleware attaches:
   - request id (`X-Request-ID`)
   - structured request log context
3. Route handler:
   - validates request via Pydantic schema
   - resolves dependencies (`UserService`, DB session)
4. Service layer method executes use-case
5. Service calls repository methods to query/write DB
6. Commit/rollback occurs at request boundary via `get_db_session` dependency
7. Response is returned via Pydantic response model
8. Exceptions are caught by global handlers (uniform error payload)

---

## Dependency flow (DI principles)

- **API depends on services**
- **Services depend on repositories**
- **Repositories depend on DB session**
- **DB session depends on settings**

We avoid “lower layers importing higher layers” to keep the architecture clean and testable.

---

## Scaling guidance (later)

### Add a new module (feature)
- Create:
  - `models/<entity>.py`
  - `schemas/<entity>.py`
  - `repositories/<entity>_repository.py`
  - `services/<entity>_service.py`
  - `api/routes/v1/<entity>.py`
- Include router in `api/routes/api_v1.py`

### Performance scaling
- Add caching layer (Redis) and cache-aside patterns in services
- Introduce read replicas; keep repositories as the adaptation layer
- Add background jobs (Celery/RQ/Arq) for heavy tasks

### Microservice extraction readiness
Because feature code is isolated (routes + service + repository), extracting a module into a standalone service typically becomes:
- move its module folder(s) into a new repo/container
- keep API contracts (schemas) stable
- replace repository with client calls (or split DB)

---

## Local development

### Using Docker compose
```bash
cd CN-Backend-23732
cp .env.example .env
make up
```

### Without Docker (manual)
Requires PostgreSQL running and env vars set.
```bash
cd CN-Backend-23732
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

---

## Database connectivity check (local)

Use this when you need to verify your current `.env` Postgres settings (including Supabase) from your machine.

### 1) Ensure your env vars are set

```bash
cd CN-Backend-23732
cp .env.example .env
# Edit .env and set:
# POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

### 2) Create/activate a virtualenv and install deps

```bash
cd CN-Backend-23732
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Run the DB connectivity check script

The script prints resolved host/port/db/user (never prints password), does a TCP reachability probe, then runs `SELECT 1`.

Run it from the backend folder:

```bash
cd CN-Backend-23732
python scripts/check_db_connection.py
```

Or run it from the repo root (also works):

```bash
python CN-Backend-23732/scripts/check_db_connection.py
```

### Exit codes

- `0`: success (TCP + `SELECT 1`)
- `2`: DNS/TCP reachability failed
- `3`: DB-level failure (auth/SSL/DB error)

## Supabase notes: Errno 101 / IPv4 vs IPv6 / pooler

If you see an error like:

```
OSError: [Errno 101] Network is unreachable
```

that is almost always a **network path** problem, not a SQLAlchemy bug.

### Common causes & mitigations

1) **Runtime has no outbound internet / egress is blocked**
   - Some hosted/container runtimes block outbound access to the public internet.
   - Mitigation: run the check from a machine/network that can reach Supabase on port `5432`, or use an allowed egress path (VPN/NAT), or move the DB into the same VPC/network as the runtime.

2) **IPv6-first DNS resolution but no IPv6 route**
   - Some environments resolve `db.<ref>.supabase.co` to IPv6 first, but do not have IPv6 routes, causing `Errno 101`.
   - Mitigations:
     - Prefer a network with working IPv6, **or**
     - Use a Supabase endpoint/hostname that resolves to IPv4 in your environment, **or**
     - Use the Supabase **connection pooler** endpoint (often works better across restrictive networks).

3) **Use Supabase pooler when you need fewer connections or better compatibility**
   - If direct connections are unreliable (or you need to reduce connection counts), use Supabase’s pooler endpoint/port as provided in the Supabase dashboard.
   - When using the pooler, update your `.env` to the pooler `POSTGRES_HOST` and `POSTGRES_PORT` values and rerun the script.

### Which host should I use?

In `.env.example` we recommend the Supabase “Database settings” host (typically `db.<project-ref>.supabase.co`).
If that host fails in your environment due to network/IPv6 constraints, try the **pooler** host shown in Supabase and re-run:

```bash
python CN-Backend-23732/scripts/check_db_connection.py
```

## Testing

```bash
cd CN-Backend-23732
make test
```

- Tests use `httpx.AsyncClient` against the ASGI app.
- DB tests rely on a dedicated database schema (by default the same DB but separate DB name via env).

---

## Security & production notes (baseline)

- Do not log secrets or request bodies by default.
- Enable CORS only for known origins in production.
- Terminate TLS at ingress (e.g., ALB/Nginx) or use a TLS-enabled proxy container.
- Run migrations explicitly in CI/CD (not auto-run on app boot in production).

---
