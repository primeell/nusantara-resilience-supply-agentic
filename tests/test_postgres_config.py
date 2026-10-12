"""Configuration-only tests for optional Cloud Foundry PostgreSQL discovery."""

from __future__ import annotations

import json

from backend.repository import _postgres_dsn_from_env


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
