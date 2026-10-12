"""Small read-only A2A boundary for the NSRA Joule capability."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from backend.analytics import portfolio_items
from backend.repository import InMemoryRepository
from backend.service import run_deterministic_analysis


PROTOCOL_VERSION = "0.3.0"
AGENT_NAME = "nsra_supply_resilience_agent"


def agent_card(base_url: str) -> dict[str, Any]:
    """Return a discoverable A2A agent card without any credential data."""

    return {
        "protocolVersion": PROTOCOL_VERSION,
        "name": "NSRA Supply Resilience Agent",
        "description": (
            "Provides grounded, read-only disruption briefings and deterministic "
            "mitigation recommendations for the NSRA synthetic supply-chain dataset."
        ),
        "url": f"{base_url.rstrip('/')}/a2a",
        "version": "1.0.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
        "skills": [
            {
                "id": "supply-resilience-briefing",
                "name": "Supply resilience briefing",
                "description": (
                    "Summarizes a known disruption and its deterministic mitigation "
                    "recommendation. It uses synthetic demo data and never executes ERP actions."
                ),
                "tags": ["supply-chain", "incident", "inventory", "mitigation"],
                "examples": [
                    "Brief me on the highest-priority supply disruption.",
                    "What is the recommended response for INC-MKS-FOUR-DAY?",
                ],
            }
        ],
    }


def handle_message(payload: dict[str, Any], repo: InMemoryRepository) -> dict[str, Any]:
    """Handle the constrained A2A ``message/send`` interaction.

    The adapter intentionally invokes only the deterministic planner with
    ``persist=False``. It cannot create approval packages, execute ERP actions,
    mutate inventory, or invoke public live AI inference.
    """

    request_id = payload.get("id")
    if payload.get("jsonrpc") != "2.0":
        return _error(request_id, -32600, "JSON-RPC version 2.0 is required")
    if payload.get("method") != "message/send":
        return _error(request_id, -32601, "Only message/send is supported")

    params = payload.get("params")
    if not isinstance(params, dict):
        return _error(request_id, -32602, "params must be an object")
    message = params.get("message")
    if not isinstance(message, dict):
        return _error(request_id, -32602, "params.message must be an object")

    text = _message_text(message)
    incident_id = _incident_for_text(text, repo)
    try:
        analysis = run_deterministic_analysis(
            repo,
            incident_id=incident_id,
            persist=False,
        )
    except LookupError:
        return _error(request_id, -32602, "No valid NSRA incident was found")

    recommendation = next(
        item
        for item in analysis.scenarios
        if item.scenario_id == analysis.recommended_scenario_id
    )
    context_id = str(
        message.get("contextId") or params.get("contextId") or uuid4()
    )
    task_id = str(message.get("taskId") or params.get("taskId") or uuid4())
    reply = "\n".join(
        [
            "## NSRA supply resilience briefing",
            f"**Incident:** {analysis.incident_id}",
            f"**Recommended response:** {recommendation.name} ({recommendation.scenario_id})",
            f"**Modeled downtime:** {recommendation.simulation.downtime_hours:.1f}h "
            f"versus {analysis.baseline.simulation.downtime_hours:.1f}h baseline.",
            f"**Modeled total impact:** IDR {recommendation.cost_breakdown.total_idr:,.0f}.",
            f"**Rationale:** {analysis.recommendation_rationale}",
            "**Control:** This briefing uses synthetic data and is read-only; human approval "
            "is required before any operational action.",
        ]
    )
    assistant_message = {
        "kind": "message",
        "role": "agent",
        "messageId": str(uuid4()),
        "parts": [{"kind": "text", "text": reply}],
    }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "kind": "task",
            "id": task_id,
            "contextId": context_id,
            "status": {
                "state": "completed",
                "timestamp": datetime.now(UTC).isoformat(),
                # Joule Studio reads the final remote-agent answer here. Keep
                # the artifact below as the canonical output for A2A clients.
                "message": assistant_message,
            },
            "history": [
                {
                    "kind": "message",
                    "role": "user",
                    "messageId": str(message.get("messageId") or uuid4()),
                    "parts": [{"kind": "text", "text": text}],
                }
            ],
            "artifacts": [
                {
                    "artifactId": str(uuid4()),
                    "name": "nsra_supply_resilience_briefing",
                    "parts": [{"kind": "text", "text": reply}],
                }
            ],
        },
    }


def _message_text(message: dict[str, Any]) -> str:
    parts = message.get("parts", [])
    if not isinstance(parts, list):
        return ""
    return " ".join(
        str(part.get("text", ""))[:1200]
        for part in parts
        if isinstance(part, dict) and part.get("kind") == "text"
    )


def _incident_for_text(text: str, repo: InMemoryRepository) -> str:
    normalized = text.upper()
    incidents = repo.list_incidents()
    for incident in incidents:
        if incident.incident_id.upper() in normalized:
            return incident.incident_id
    priority_portfolio = portfolio_items(repo)
    prioritized = next((item for item in priority_portfolio if item["active"]), None)
    if prioritized is None:
        return incidents[0].incident_id
    return str(prioritized["incident_id"])


def _error(request_id: object, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }
