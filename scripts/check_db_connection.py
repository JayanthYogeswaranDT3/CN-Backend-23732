from __future__ import annotations

import asyncio
import os
import socket
import sys
from urllib.parse import urlsplit

from sqlalchemy import text

#
# Ensure `src.*` imports work when running this script directly from any cwd.
# Without this, users commonly see: ModuleNotFoundError: No module named 'src'
#
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from src.core.settings import get_settings
from src.db.session import engine


# PUBLIC_INTERFACE
def main() -> None:
    """
    Check whether the backend can reach and connect to the configured Postgres database.

    This script:
    1) Prints the resolved DB host/port/db/user (never prints password).
    2) Performs a DNS + TCP reachability probe to host:port.
    3) Executes a lightweight "SELECT 1" using the app's SQLAlchemy async engine.

    Exit codes:
    - 0: success
    - 2: network/DNS/TCP reachability problem
    - 3: DB connection/auth/SSL/DB-level error
    """
    settings = get_settings()

    # Do not print secrets. Derive host/port/db from the resolved SQLAlchemy URL,
    # so this script works whether config comes from POSTGRES_CONNECTION or discrete env vars.
    parts = urlsplit(settings.database_url)
    print(f"DB url scheme: {parts.scheme}")
    print(f"DB host: {parts.hostname}")
    print(f"DB port: {parts.port}")
    print(f"DB name: {(parts.path or '').lstrip('/')}")
    # Only show whether creds exist, never the actual values.
    print(f"DB user set: {bool(parts.username or settings.postgres_user)}")
    print(f"DB password set: {bool(parts.password or settings.postgres_password)}")

    # 1) DNS + TCP reachability
    try:
        if not parts.hostname or not parts.port:
            raise RuntimeError("Could not parse DB host/port from settings.database_url")
        addrinfo = socket.getaddrinfo(parts.hostname, parts.port, type=socket.SOCK_STREAM)
        # Pick first resolved address
        family, socktype, proto, _, sockaddr = addrinfo[0]
        with socket.socket(family, socktype, proto) as s:
            s.settimeout(5)
            s.connect(sockaddr)
        print("Reachability: OK (TCP connect succeeded)")
    except Exception as e:
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
        print(f"DB query: FAILED ({type(e).__name__}: {e})")
        raise SystemExit(3) from e


if __name__ == "__main__":
    main()
