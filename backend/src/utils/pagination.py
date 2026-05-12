from __future__ import annotations


# PUBLIC_INTERFACE
def clamp_limit(limit: int, min_value: int = 1, max_value: int = 100) -> int:
    """Clamp an integer between min and max values."""
    return max(min_value, min(limit, max_value))
