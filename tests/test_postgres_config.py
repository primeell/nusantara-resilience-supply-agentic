"""Configuration-only tests for optional Cloud Foundry PostgreSQL discovery."""

from __future__ import annotations

import json

import pytest

from backend import repository as repository_module
from backend.repository import (
    _postgres_dsn_from_env,
    _postgres_sslmode_from_env,
    _state_backend_from_env,
)


def test_direct_database_url_takes_precedence(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DATABASE_URL", "postgresql://direct.example/nsra")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://fallback.example/nsra")

    assert _postgres_dsn_from_env() == "postgresql://direct.example/nsra"


def test_bound_postgres_service_is_discovered(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.setenv(
        "VCAP_SERVICES",
        json.dumps(
            {
                "postgresql-db": [
                    {
                        "name": "nsra-postgres",
                        "tags": ["postgresql", "relational"],
                        "credentials": {"uri": "postgresql://bound.example/nsra"},
                    }
                ]
            }
        ),
    )

    assert _postgres_dsn_from_env() == "postgresql://bound.example/nsra"


def test_invalid_vcap_services_is_ignored(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.setenv("VCAP_SERVICES", "not-json")

    assert _postgres_dsn_from_env() is None


def test_postgresql_backend_fails_closed_without_dsn(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("NSRA_STATE_BACKEND", "postgresql")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("VCAP_SERVICES", raising=False)

    with pytest.raises(RuntimeError, match="PostgreSQL is required"):
        repository_module.build_repository()


def test_explicit_sqlite_backend_ignores_postgres_dsn(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("NSRA_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("DATABASE_URL", "postgresql://must-not-connect.example/nsra")
    monkeypatch.setenv("NSRA_STATE_DB_PATH", str(tmp_path / "explicit.sqlite3"))

    selected = repository_module.build_repository()

    assert selected.storage_name == "sqlite"


def test_invalid_state_backend_is_rejected(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("NSRA_STATE_BACKEND", "redis")

    with pytest.raises(RuntimeError, match="NSRA_STATE_BACKEND"):
        _state_backend_from_env()


def test_production_defaults_to_postgresql_and_requires_tls(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("NSRA_STATE_BACKEND", raising=False)
    monkeypatch.delenv("NSRA_POSTGRES_SSLMODE", raising=False)

    assert _state_backend_from_env() == "postgresql"
    assert _postgres_sslmode_from_env() == "require"


def test_production_rejects_unencrypted_postgres(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("NSRA_POSTGRES_SSLMODE", "disable")

    with pytest.raises(RuntimeError, match="must require TLS"):
        _postgres_sslmode_from_env()
