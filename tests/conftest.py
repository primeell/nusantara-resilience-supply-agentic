"""Shared deterministic fixtures for the NSRA test suite."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest

# Keep test resets isolated from a concurrently running demo service.
TEST_STATE_PATH = Path(tempfile.gettempdir()) / f"nsra-pytest-{os.getpid()}.sqlite3"
os.environ["NSRA_STATE_BACKEND"] = "sqlite"
os.environ.setdefault("NSRA_STATE_DB_PATH", str(TEST_STATE_PATH))

from backend.main import app  # noqa: E402
from backend.repository import repository  # noqa: E402


@pytest.fixture(autouse=True)
def reset_demo_repository() -> Iterator[None]:
    repository.reset()
    yield
    repository.reset()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=5,
    ) as client:
        yield client
