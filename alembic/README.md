# Alembic Migrations

This scaffold includes Alembic configuration wired to `app.db.base.Base.metadata`.

Typical workflow:
1) Start containers: `make up`
2) Create migration: `make migrate MSG="create items"`
3) Apply migration: `make upgrade`

Notes:
- Autogenerate depends on importing model metadata.
- Ensure your models are importable and included in `Base.metadata` (in this scaffold they are via `app.modules.items.models` import when you run the app or migrations).
"
