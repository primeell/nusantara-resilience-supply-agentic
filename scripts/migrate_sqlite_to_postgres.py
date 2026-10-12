"""Copy one validated NSRA SQLite snapshot into PostgreSQL.

The destination DSN is read from the environment or the ignored local `.env`
file. It is never accepted as a command-line argument or printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = PROJECT_ROOT / ".nsra-local" / "nsra-state.sqlite3"
ALLOWED_ENTITY_TYPES = {"incident", "analysis", "draft", "audit"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate an NSRA SQLite state snapshot to PostgreSQL."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an already initialized destination snapshot",
    )
    return parser


def _read_source(path: Path) -> tuple[list[tuple[str, str, str]], dict[str, str]]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise SystemExit(f"SQLite source does not exist: {resolved}")

    uri = resolved.as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
            rows = connection.execute(
                "SELECT entity_type, entity_id, payload FROM entity_state"
            ).fetchall()
            meta = dict(
                connection.execute(
                    "SELECT meta_key, meta_value FROM repository_meta"
                ).fetchall()
            )
    except sqlite3.Error as exc:
        raise SystemExit(f"SQLite source is not a valid NSRA state store: {exc}") from None

    if meta.get("initialized") != "1":
        raise SystemExit("SQLite source is not initialized.")
    for entity_type, entity_id, payload in rows:
        if entity_type not in ALLOWED_ENTITY_TYPES or not entity_id:
            raise SystemExit("SQLite source contains an unsupported state row.")
        try:
            json.loads(payload)
        except json.JSONDecodeError:
            raise SystemExit("SQLite source contains invalid JSON state.") from None
    return rows, meta


def main() -> int:
    args = _parser().parse_args()
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL or POSTGRES_URL is not configured.")

    rows, meta = _read_source(args.source)
    sslmode = os.getenv("NSRA_POSTGRES_SSLMODE", "require")
    try:
        with psycopg.connect(
            dsn,
            connect_timeout=10,
            application_name="nsra-state-migration",
            sslmode=sslmode,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("nsra-state",))
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entity_state (
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        PRIMARY KEY (entity_type, entity_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS repository_meta (
                        meta_key TEXT PRIMARY KEY,
                        meta_value TEXT NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "SELECT meta_value FROM repository_meta WHERE meta_key = 'initialized'"
                )
                initialized = cursor.fetchone()
                if initialized and initialized[0] == "1" and not args.force:
                    raise SystemExit(
                        "Destination is already initialized; rerun with --force only after review."
                    )

                cursor.execute("DELETE FROM entity_state")
                cursor.executemany(
                    """
                    INSERT INTO entity_state(entity_type, entity_id, payload)
                    VALUES (%s, %s, %s)
                    """,
                    rows,
                )
                cursor.execute("DELETE FROM repository_meta")
                cursor.executemany(
                    """
                    INSERT INTO repository_meta(meta_key, meta_value)
                    VALUES (%s, %s)
                    """,
                    list(meta.items()),
                )
                cursor.execute("SELECT COUNT(*) FROM entity_state")
                migrated_count = int(cursor.fetchone()[0])
                if migrated_count != len(rows):
                    raise RuntimeError("destination row count does not match the source")
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(
            f"PostgreSQL migration failed ({type(exc).__name__}); no credentials were printed."
        ) from None

    print(f"Migrated and verified {migrated_count} NSRA state rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
