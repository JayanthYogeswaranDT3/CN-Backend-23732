from __future__ import annotations

import asyncio
import os
import socket
import sys
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import text

#
# Ensure `src.*` imports work when running this script directly from any cwd.
# Without this, users commonly see: ModuleNotFoundError: No module named 'src'
#
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from src.core.settings import get_settings  # noqa: E402
from src.db.session import engine  # noqa: E402


def _redact_db_url(url: str) -> str:
    """Return a redacted form of a DB URL (never logs username/password)."""
    parts = urlsplit(url)

    # Remove userinfo from netloc: "user:pass@host:port" -> "host:port"
    netloc = parts.netloc
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]

    # Remove sensitive query params that sometimes include secrets.
    # Keep sslmode visible since it's useful for debugging connectivity.
    if parts.query:
        safe_pairs: list[tuple[str, str]] = []
        for kv in parts.query.split("&"):
            if not kv:
                continue
            k = kv.split("=", 1)[0].lower().strip()
            if k in {"password", "pass", "pwd", "secret", "token", "apikey", "api_key"}:
                continue
            safe_pairs.append(tuple(kv.split("=", 1)) if "=" in kv else (kv, ""))

        # Rebuild query in a stable way; avoid importing parse_qsl/urlencode just for logs.
        query = "&".join([f"{k}={v}" if v != "" else k for k, v in safe_pairs])
    else:
        query = ""

    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))

def _safe_str(v: object) -> str:
    """Return a safe string representation for diagnostics (never raises)."""
    try:
        return "" if v is None else str(v)
    except Exception:
        return "<unprintable>"


def _env_has_postgres_connection() -> bool:
    """Return True if POSTGRES_CONNECTION is present and non-empty in the environment."""
    return bool(os.getenv("POSTGRES_CONNECTION", "").strip())


def _get_authoritative_db_url_source() -> str:
    """
    Decide which env var source should be treated as authoritative.

    We explicitly prefer POSTGRES_CONNECTION if set, and only fall back to legacy
    discrete POSTGRES_* variables when POSTGRES_CONNECTION is empty.
    """
    if _env_has_postgres_connection():
        return "POSTGRES_CONNECTION"
    # Keep wording generic to avoid leaking/mentioning legacy/Supabase specifics in logs.
    return "fallback discrete POSTGRES_* (POSTGRES_CONNECTION not set)"


def _infer_port(parts) -> int | None:
    """
    Infer the port from a parsed DB URL.

    Some managed Postgres providers (including Neon) commonly omit the explicit port
    in the URI; in that case Postgres defaults to 5432.
    """
    if parts.port is not None:
        return parts.port
    # Only default when a hostname is present; otherwise parsing failed.
    if parts.hostname:
        return 5432
    return None


def _resolve_db_url_for_script(settings) -> tuple[str, str]:
    """
    Resolve the DB URL this script should use, plus a human-friendly source label.

    We *explicitly* prefer POSTGRES_CONNECTION so the script's behavior and diagnostics
    match the user's expectation even if other env vars exist.
    """
    if _env_has_postgres_connection():
        # Settings.database_url already normalizes to SQLAlchemy asyncpg URL.
        return settings.database_url, "POSTGRES_CONNECTION"
    return settings.database_url, "fallback discrete POSTGRES_* (POSTGRES_CONNECTION not set)"


# PUBLIC_INTERFACE
def main() -> None:
    """
    Check whether the backend can reach and connect to the configured Postgres database.

    Authoritative config:
    - If POSTGRES_CONNECTION is set, it is treated as the authoritative DB connection source.
    - Otherwise, the backend falls back to legacy discrete POSTGRES_* settings.

    This script:
    1) Prints a sanitized (redacted) view of the resolved DB URL details (never prints secrets).
    2) Performs a DNS + TCP reachability probe to host:port.
    3) Executes a lightweight "SELECT 1" using the app's SQLAlchemy async engine.

    Exit codes:
    - 0: success
    - 2: network/DNS/TCP reachability problem
    - 3: DB connection/auth/SSL/DB-level error
    """
    settings = get_settings()

    resolved_url, source = _resolve_db_url_for_script(settings)
    if not isinstance(resolved_url, str) or not resolved_url.strip():
        # Fail fast with actionable info rather than letting SQLAlchemy raise TypeError later.
        print("DB config source:", source)
        print("DB url (redacted): <missing/empty>")
        print("ERROR: Resolved database URL is missing or not a string.")
        print("Hint: set POSTGRES_CONNECTION to your Neon URI (postgresql://USER:PASSWORD@HOST/DB?sslmode=require).")
        raise SystemExit(3)

    parts = urlsplit(resolved_url)
    port = _infer_port(parts)

    print(f"DB config source: {source}")
    print(f"DB env POSTGRES_CONNECTION set: {_env_has_postgres_connection()}")
    print(f"DB url (redacted): {_redact_db_url(resolved_url)}")
    print(f"DB url scheme: {_safe_str(parts.scheme)}")
    print(f"DB host: {_safe_str(parts.hostname)}")
    print(f"DB port: {port}")
    print(f"DB name: {(parts.path or '').lstrip('/')}")
    # Only show whether creds exist, never the actual values.
    print(f"DB user set: {bool(parts.username or settings.postgres_user)}")
    print(f"DB password set: {bool(parts.password or settings.postgres_password)}")

    # 1) DNS + TCP reachability
    try:
        if not parts.hostname or not port:
            raise RuntimeError("Could not parse DB host/port from resolved database URL.")
        addrinfo = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
        # Pick first resolved address
        family, socktype, proto, _, sockaddr = addrinfo[0]
        with socket.socket(family, socktype, proto) as s:
            s.settimeout(5)
            s.connect(sockaddr)
        print("Reachability: OK (TCP connect succeeded)")
    except Exception as e:
        # Never print the raw URL or env vars in error paths.
        print(f"Reachability: FAILED ({type(e).__name__}: {e})")
        raise SystemExit(2) from e

    # 2) DB-level check (SELECT 1)
    async def _db_check() -> None:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        asyncio.run(_db_check())
        print("DB query: OK (SELECT 1 succeeded)")
        raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        # Avoid echoing connection string; SQLAlchemy exceptions can include it in some cases,
        # but typically do not. We keep the message minimal and type-only for safety.
        print(f"DB query: FAILED ({type(e).__name__}: {_safe_str(e)})")
        raise SystemExit(3) from e


if __name__ == "__main__":
    main()
