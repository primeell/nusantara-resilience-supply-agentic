"""Dashboard-to-backend client behavior without a running browser."""

from __future__ import annotations

import pytest

from dashboard.api_client import APIError, NSRAApiClient


class FakeResponse:
    def __init__(self, payload: dict[str, object], *, ok: bool = True, status: int = 200):
        self.payload = payload
        self.ok = ok
        self.status_code = status

    def json(self) -> dict[str, object]:
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.response


def test_dashboard_client_uses_versioned_backend_contract() -> None:
    session = FakeSession(FakeResponse({"incidents": []}))
    client = NSRAApiClient("http://localhost:9000/", timeout=3, session=session)  # type: ignore[arg-type]
    payload = client.incidents()

    assert payload == {"incidents": []}
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"] == "http://localhost:9000/api/v1/incidents"
    assert session.calls[0]["timeout"] == 3


def test_dashboard_client_surfaces_safe_error_reference() -> None:
    session = FakeSession(
        FakeResponse(
            {
                "error_code": "NOT_FOUND",
                "message": "Incident not found",
                "trace_id": "trace-safe",
            },
            ok=False,
            status=404,
        )
    )
    client = NSRAApiClient(session=session)  # type: ignore[arg-type]
    with pytest.raises(APIError, match="NOT_FOUND.*trace-safe"):
        client.analyze("MISSING")
