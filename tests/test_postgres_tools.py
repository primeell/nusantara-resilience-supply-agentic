"""Regression checks for safe PostgreSQL operator helpers."""

from __future__ import annotations

import json
import sqlite3

import pytest

from scripts.migrate_sqlite_to_postgres import _read_source


def test_migration_reader_accepts_initialized_nsra_snapshot(tmp_path) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "state.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE entity_state "
            "(entity_type TEXT, entity_id TEXT, payload TEXT)"
        )
        connection.execute(
            "CREATE TABLE repository_meta (meta_key TEXT, meta_value TEXT)"
        )
        connection.execute(
            "INSERT INTO entity_state VALUES (?, ?, ?)",
            ("incident", "INC-1", json.dumps({"incident_id": "INC-1"})),
        )
        connection.execute("INSERT INTO repository_meta VALUES ('initialized', '1')")

    rows, meta = _read_source(source)

    assert len(rows) == 1
    assert meta["initialized"] == "1"


def test_migration_reader_rejects_invalid_json(tmp_path) -> None:  # type: ignore[no-untyped-def]
    source = tmp_path / "invalid.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute(
            "CREATE TABLE entity_state "
            "(entity_type TEXT, entity_id TEXT, payload TEXT)"
        )
        connection.execute(
            "CREATE TABLE repository_meta (meta_key TEXT, meta_value TEXT)"
        )
        connection.execute(
            "INSERT INTO entity_state VALUES ('incident', 'INC-1', 'not-json')"
        )
        connection.execute("INSERT INTO repository_meta VALUES ('initialized', '1')")

    with pytest.raises(SystemExit, match="invalid JSON"):
        _read_source(source)


def test_postgres_helpers_do_not_print_database_url() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    configure = (root / "scripts" / "configure_postgres_runtime.py").read_text(
        encoding="utf-8"
    )
    check = (root / "scripts" / "test_postgres_connection.py").read_text(
        encoding="utf-8"
    )

    assert "print(database_url)" not in configure
    assert "print(dsn)" not in check
    assert "DATABASE_URL" in configure
