# Backend (FastAPI) — Clean Modular Architecture (No Docker)

This backend scaffold implements a **clean modular architecture** using:

- Python **>= 3.11**
- FastAPI **>= 0.110** (pinned to `0.115.7` per workspace constraints)
- Pydantic **v2** (pinned to `2.10.6`)
- SQLAlchemy **v2** async (pinned to `2.0.37`)
- PostgreSQL (run locally, no Docker required)
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
CN-Backend-23732/
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

### `src/services/` — business logic / orchestration
**Purpose**
- Implements use-cases (e.g., “create user”, “list users”) and orchestrates repositories.

### `src/repositories/` — data access (repository pattern)
**Purpose**
- Encapsulates persistence concerns (SQLAlchemy queries) behind a stable interface.

### `src/models/` — persistence models (SQLAlchemy ORM)
**Purpose**
- SQLAlchemy ORM models describing tables.

### `src/schemas/` — DTOs (Pydantic v2 models)
**Purpose**
- Input/output contracts for API and service boundaries.

### `src/core/` — configuration + cross-cutting infrastructure
**Purpose**
- Settings, logging configuration, lifecycle hooks, and security utilities.

### `src/db/` — database session management + base metadata
**Purpose**
- SQLAlchemy engine/session creation, DB initialization.

### `src/utils/` — small shared helpers
**Purpose**
- Small stateless helpers used across modules.

### `alembic/` and `alembic.ini` — migrations
**Purpose**
- Database schema migrations.

---

## Request flow (end-to-end)

1. Incoming request hits FastAPI (`src/api/main.py`)
2. Middleware attaches:
   - request id (`X-Request-ID`)
   - structured request log context
3. Route handler:
   - validates request via Pydantic schema
   - resolves dependencies (Service, DB session)
4. Service layer method executes use-case
5. Service calls repository methods to query/write DB
6. Commit/rollback occurs at request boundary via DB session dependency
7. Response is returned via Pydantic response model
8. Exceptions are caught by global handlers (uniform error payload)

---

## Local development (no Docker)

### 1) Prerequisites
- Python 3.11+
- A running PostgreSQL instance you can connect to (local Postgres, cloud Postgres, Supabase Postgres, etc.)

### 2) Configure environment
Create a `.env` file from the example and set your Postgres connection values:

```bash
cd CN-Backend-23732
cp .env.example .env
# Edit .env and set:
# POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

### 3) Create a virtual environment + install deps
```bash
cd CN-Backend-23732
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Run the API (dev / reload)
```bash
cd CN-Backend-23732
source .venv/bin/activate
make dev
```

The API will be available at:

- **API base**: `http://localhost:8000`
- **Swagger UI** (interactive docs): `http://localhost:8000/docs`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

> Note: this project also uses an `API_V1_PREFIX` env var (defaults to `/api/v1`).  
> Example endpoints will typically be under `http://localhost:8000/api/v1/...`.

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

---

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

---

## Testing
```bash
cd CN-Backend-23732
source .venv/bin/activate
make test
```

---

## Security & production notes (baseline)

- Do not log secrets or request bodies by default.
- Enable CORS only for known origins in production.
- Terminate TLS at ingress (e.g., ALB/Nginx) or use a TLS-enabled proxy.
- Run migrations explicitly in CI/CD (not auto-run on app boot in production).
