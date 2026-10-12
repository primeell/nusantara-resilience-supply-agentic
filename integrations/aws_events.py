"""Side-effect-free AWS EventBridge/Lambda contract adapter.

The module deliberately performs no AWS API calls. It accepts the shape emitted
by EventBridge, validates it through the same Pydantic contract as the HTTP API,
and can feed a caller-provided repository for local Lambda emulation.
"""

from __future__ import annotations

from typing import Any

from backend.repository import InMemoryRepository, repository
from backend.schemas import IncidentCreateRequest
from backend.service import ingest_incident


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return the transport metadata and detail without calling AWS."""

    detail = event.get("detail", {})
    if not isinstance(detail, dict):
        raise ValueError("EventBridge detail must be an object")
    return {
        "id": event.get("id"),
        "source": event.get("source", "unknown"),
        "detail_type": event.get("detail-type", "unknown"),
        "time": event.get("time"),
        "detail": detail,
    }


def eventbridge_to_incident(event: dict[str, Any]) -> IncidentCreateRequest:
    """Translate a bounded EventBridge event into the canonical incident model."""

    normalized = normalize_event(event)
    detail = normalized["detail"]
    detected_at = detail.get("detected_at") or normalized["time"]
    payload = {
        "incident_id": detail.get("incident_id") or normalized["id"],
        "source": normalized["source"],
        "event_type": detail.get("event_type") or normalized["detail_type"],
        "severity": detail.get("severity"),
        "title": detail.get("title"),
        "description": detail.get("description", ""),
        "shipment_id": detail.get("shipment_id"),
        "detected_at": detected_at,
        "delay_hours": detail.get("delay_hours", 0),
    }
    return IncidentCreateRequest.model_validate(payload)


def lambda_handler(
    event: dict[str, Any],
    context: Any,
    *,
    repo: InMemoryRepository = repository,
) -> dict[str, Any]:
    """Locally emulatable Lambda handler with idempotent incident ingestion."""

    request = eventbridge_to_incident(event)
    incident, created = ingest_incident(repo, request)
    return {
        "statusCode": 201 if created else 200,
        "body": {
            "mode": "local-emulation",
            "created": created,
            "incident_id": incident.incident_id,
            "aws_api_called": False,
        },
    }
