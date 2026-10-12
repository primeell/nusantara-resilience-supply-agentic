"""Verify the configured PostgreSQL endpoint without revealing its DSN."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL or POSTGRES_URL is not configured.")

    sslmode = os.getenv("NSRA_POSTGRES_SSLMODE", "require")
    try:
        with psycopg.connect(
            dsn,
            connect_timeout=10,
            application_name="nsra-connection-check",
            sslmode=sslmode,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SHOW server_version")
                version = str(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl "
                    "WHERE pid = pg_backend_pid()), false)"
                )
                tls_active = bool(cursor.fetchone()[0])
    except Exception as exc:
        # Driver messages can echo connection details. Keep the public failure
        # deliberately generic and let operators inspect the database console.
        raise SystemExit(
            f"PostgreSQL connection failed ({type(exc).__name__}); no credentials were printed."
        ) from None

    if sslmode in {"require", "verify-ca", "verify-full"} and not tls_active:
        raise SystemExit("PostgreSQL responded without the required TLS session.")

    print(f"PostgreSQL connection verified (server {version}; TLS active: {tls_active}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
