"""A2A contract tests for the read-only Joule boundary."""

from __future__ import annotations

import httpx
import pytest


pytestmark = pytest.mark.anyio


async def test_agent_card_is_discoverable(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/.well-known/agent.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["protocolVersion"] == "0.3.0"
    assert payload["url"].endswith("/a2a")
    assert payload["skills"][0]["id"] == "supply-resilience-briefing"


async def test_a2a_returns_a_read_only_grounded_briefing(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/a2a",
        json={
            "jsonrpc": "2.0",
            "id": "test-request",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Brief me on INC-MKS-FOUR-DAY.",
                        }
                    ],
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    task = payload["result"]
    message = task["artifacts"][0]["parts"][0]["text"]
    assert payload["id"] == "test-request"
    assert task["kind"] == "task"
    assert task["status"]["state"] == "completed"
    assert task["status"]["timestamp"]
    assert task["status"]["message"]["role"] == "agent"
    assert task["status"]["message"]["parts"][0]["text"] == message
    assert task["history"][0]["kind"] == "message"
    assert task["history"][0]["messageId"]
    assert "INC-MKS-FOUR-DAY" in message
    assert "read-only" in message


async def test_a2a_selects_highest_priority_incident_without_an_explicit_id(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/a2a",
        json={
            "jsonrpc": "2.0",
            "id": "priority-request",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "kind": "text",
                            "text": "What is the highest-priority supply incident?",
                        }
                    ],
                }
            },
        },
    )

    assert response.status_code == 200
    message = response.json()["result"]["artifacts"][0]["parts"][0]["text"]
    assert "INC-SRG-NO-FEASIBLE" in message


async def test_a2a_rejects_unknown_methods(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/a2a",
        json={"jsonrpc": "2.0", "id": "bad", "method": "tasks/cancel"},
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == -32601
