"""Contract tests for local AWS emulation and SAP-shaped draft mapping."""

from __future__ import annotations

import pytest

from backend.repository import InMemoryRepository
from backend.schemas import TransactionDraftCreateRequest
from backend.service import create_transaction_draft, run_deterministic_analysis
from integrations.aws_events import eventbridge_to_incident, lambda_handler
from integrations.sap_adapter import to_sap_draft_payload


def _event() -> dict[str, object]:
    return {
        "version": "0",
        "id": "INC-EVB-001",
        "detail-type": "VESSEL_DELAY",
        "source": "local.nsra.event-simulator",
        "time": "2026-10-10T09:00:00+08:00",
        "detail": {
            "severity": "HIGH",
            "title": "Locally emulated vessel delay",
            "description": "EventBridge-compatible fixture; not a live AWS event.",
            "shipment_id": "SHP-MKS-001",
            "delay_hours": 12,
        },
    }


def test_eventbridge_event_normalizes_to_canonical_incident() -> None:
    request = eventbridge_to_incident(_event())
    assert request.incident_id == "INC-EVB-001"
    assert request.source == "local.nsra.event-simulator"
    assert request.event_type == "VESSEL_DELAY"
    assert request.detected_at.isoformat() == "2026-10-10T09:00:00+08:00"


def test_local_lambda_handler_is_idempotent_and_calls_no_aws_api() -> None:
    repo = InMemoryRepository()
    first = lambda_handler(_event(), None, repo=repo)
    second = lambda_handler(_event(), None, repo=repo)
    assert first["statusCode"] == 201
    assert second["statusCode"] == 200
    assert first["body"]["aws_api_called"] is False


def test_eventbridge_rejects_non_object_detail() -> None:
    with pytest.raises(ValueError, match="detail must be an object"):
        eventbridge_to_incident({"detail": "bad"})


def test_sap_payload_is_explicitly_simulation_only() -> None:
    repo = InMemoryRepository()
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")
    draft = create_transaction_draft(
        repo,
        TransactionDraftCreateRequest(
            incident_id=analysis.incident_id,
            analysis_id=analysis.analysis_id,
            scenario_id=analysis.recommended_scenario_id,
            requested_by="integration.test",
        ),
    )
    payload = to_sap_draft_payload(draft)
    assert payload["simulationOnly"] is True
    assert payload["externalReference"] == draft.draft_id
    assert payload["documentType"] == "COMBINED"
    assert sum(item["quantity"] for item in payload["items"]) == 3000
