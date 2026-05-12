from __future__ import annotations

import uuid


# PUBLIC_INTERFACE
def new_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


# PUBLIC_INTERFACE
def new_request_id() -> str:
    """Generate a request id (UUID)."""
    return new_uuid()
