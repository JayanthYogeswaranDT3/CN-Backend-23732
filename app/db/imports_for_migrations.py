"""
This module exists to ensure that all ORM models are imported so Alembic can
discover them during autogeneration.

Import this module from Alembic env.py or app startup if needed.
"""

from app.modules.items import models as _items_models  # noqa: F401
"
