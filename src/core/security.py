from __future__ import annotations

import hashlib


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """
    Hash a password (placeholder).

    Production note:
    - Replace with passlib/bcrypt/argon2 and proper salting.
    - Kept minimal to avoid adding extra dependencies in the scaffold.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
