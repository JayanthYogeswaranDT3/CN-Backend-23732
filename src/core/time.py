from __future__ import annotations

from datetime import datetime, timezone


# PUBLIC_INTERFACE
def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)
