"""FastAPI routes for the NSRA local, demo-safe MVP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from dotenv import load_dotenv

from agent.orchestrator import run_bounded_orchestration
from agent.sap_ai_client import SAPClientError, configuration_readiness
from backend.a2a import agent_card, handle_message
from backend.analytics import network_snapshot, overview_snapshot, portfolio_items
from backend.inventory import project_disruption
from backend.mock_erp import get_inventory_item as get_legacy_inventory_item
from backend.mock_erp import get_shipment as get_legacy_shipment
from backend.repository import EntityNotFoundError, repository
from backend.schemas import (
    DisruptionAnalysisRequest,
    ErrorEnvelope,
    IncidentCreateRequest,
    ScenarioCompareRequest,
    TransactionDecisionRequest,
    TransactionDraftCreateRequest,
)
from backend.service import (
    InfeasibleDraftError,
    InvalidStateTransitionError,
    create_transaction_draft,
    decide_transaction_draft,
    ingest_incident,
    inventory_views,
    run_deterministic_analysis,
)

# Runtime loading is intentionally silent. Values remain local, are never logged,
# and existing process environment variables take precedence over the file.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
FRONTEND_ASSETS = {
    "styles.css": "text/css",
    "app.js": "application/javascript",
    "indonesia-50m.json": "application/json",
}
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env_flag(name: str, default: bool = False) -> bool:
    """Read one non-secret boolean runtime flag."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _state_persistence_scope() -> str:
    """Describe the effective store without exposing its connection details."""

    if repository.storage_name == "postgresql":
        return "durable-cloud"
    configured = os.getenv("NSRA_STATE_PERSISTENCE", "durable-local")
    if configured == "auto":
        return "ephemeral-instance"
    return configured


def _live_ai_requests_enabled() -> bool:
    """Require an explicit production opt-in before public requests reach SAP AI."""

    production = os.getenv("APP_ENV", "development").strip().casefold() == "production"
    return _env_flag("NSRA_LIVE_AI_REQUESTS_ENABLED", default=not production)


app = FastAPI(
    title="Nusantara Supply Resiliency Agent",
    version="0.5.0",
    description=(
        "Supply disruption analysis, mitigation comparison, and controlled human "
        "approval workflow. External transaction execution is disabled by default."
    ),
)

def _trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", uuid4().hex)


def _error(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    payload = ErrorEnvelope(
        error_code=error_code,
        message=message,
        details=details,
        trace_id=_trace_id(request),
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


@app.middleware("http")
async def attach_trace_id(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Attach one non-secret correlation ID to every request and response."""

    request.state.trace_id = request.headers.get("x-request-id") or uuid4().hex
    response = await call_next(request)
    response.headers["x-trace-id"] = request.state.trace_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=jsonable_encoder(exc.errors()),
    )


@app.exception_handler(EntityNotFoundError)
async def not_found_exception_handler(
    request: Request, exc: EntityNotFoundError
) -> JSONResponse:
    return _error(
        request,
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
        message=str(exc),
    )


@app.exception_handler(InfeasibleDraftError)
async def infeasible_draft_exception_handler(
    request: Request, exc: InfeasibleDraftError
) -> JSONResponse:
    return _error(
        request,
        status_code=status.HTTP_409_CONFLICT,
        error_code="DRAFT_NOT_ALLOWED",
        message=str(exc),
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_transition_exception_handler(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return _error(
        request,
        status_code=status.HTTP_409_CONFLICT,
        error_code="INVALID_STATE_TRANSITION",
        message=str(exc),
    )


@app.exception_handler(SAPClientError)
async def sap_error_exception_handler(
    request: Request, exc: SAPClientError
) -> JSONResponse:
    return _error(
        request,
        status_code=status.HTTP_502_BAD_GATEWAY,
        error_code="SAP_AI_UNAVAILABLE",
        message="The optional SAP AI explanation is unavailable.",
        details=str(exc),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return _error(
        request,
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message=str(exc.detail),
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Keep implementation details and potential secrets out of public responses.
    return _error(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nsra-api"}


@app.get("/.well-known/agent.json")
async def a2a_agent_card(request: Request) -> dict[str, Any]:
    """Publish the read-only NSRA A2A contract used by the Joule capability."""

    return agent_card(str(request.base_url).rstrip("/"))


@app.post("/a2a")
async def a2a_message(payload: dict[str, Any]) -> JSONResponse:
    """Serve constrained A2A requests for Joule; no transaction write is possible."""

    result = handle_message(payload, repository)
    return JSONResponse(status_code=200, content=jsonable_encoder(result))


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
@app.get("/overview", include_in_schema=False, response_class=HTMLResponse)
@app.get("/network", include_in_schema=False, response_class=HTMLResponse)
@app.get("/incidents", include_in_schema=False, response_class=HTMLResponse)
@app.get("/approvals", include_in_schema=False, response_class=HTMLResponse)
@app.get("/audit", include_in_schema=False, response_class=HTMLResponse)
@app.get("/integrations", include_in_schema=False, response_class=HTMLResponse)
@app.get("/incidents/{incident_id}", include_in_schema=False, response_class=HTMLResponse)
@app.get("/scenarios/{analysis_id}", include_in_schema=False, response_class=HTMLResponse)
async def product_application() -> HTMLResponse:
    """Serve the first-party operations application for every deep-link route."""

    return HTMLResponse((FRONTEND_ROOT / "index.html").read_text(encoding="utf-8"))


@app.get("/assets/{asset_name}", include_in_schema=False, response_class=Response)
async def product_asset(asset_name: str) -> Response:
    """Serve only known first-party assets; arbitrary filesystem paths are rejected."""

    media_type = FRONTEND_ASSETS.get(asset_name)
    if media_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    content = (FRONTEND_ROOT / "assets" / asset_name).read_text(encoding="utf-8")
    return Response(content=content, media_type=media_type)


@app.get("/api/v1/status")
async def application_status() -> dict[str, object]:
    """Report capabilities without returning credential values."""

    readiness = configuration_readiness()
    sap_live_verified = _env_flag("SAP_AI_LIVE_VERIFIED")
    live_ai_requests_enabled = _live_ai_requests_enabled()
    state_persistence = _state_persistence_scope()
    return {
        "application": "nsra",
        "version": app.version,
        "environment": os.getenv("APP_ENV", "development"),
        "mode": "hybrid" if sap_live_verified else "mock",
        "verification": "SAP AI LIVE VERIFIED" if sap_live_verified else "LOCAL MOCK VERIFIED",
        "data_classification": "SYNTHETIC DEMO DATA",
        "state_store": {
            "engine": repository.storage_name,
            "persistent": state_persistence in {"durable-local", "durable-cloud"},
            "scope": state_persistence,
        },
        "sap_ai": {
            "configured": all(readiness.values()),
            "fields_present": readiness,
            "live_call_performed": sap_live_verified,
            "live_requests_enabled": live_ai_requests_enabled,
        },
        "aws": {"event_flow": "locally emulated", "live_call_performed": False},
        "real_transactions_enabled": False,
    }


@app.get("/api/v1/overview")
async def executive_overview_endpoint() -> dict[str, object]:
    """Return portfolio KPIs, trends, priority incidents, and the risk matrix."""

    return {
        "mode": "mock",
        "verification": "LOCAL MOCK VERIFIED",
        "overview": overview_snapshot(repository),
    }


@app.get("/api/v1/network")
async def network_overview_endpoint() -> dict[str, object]:
    """Return geospatial facilities and shipment/mitigation route relationships."""

    return {
        "mode": "mock",
        "verification": "LOCAL MOCK VERIFIED",
        "network": network_snapshot(repository),
    }


@app.get("/api/v1/portfolio")
async def incident_portfolio_endpoint() -> dict[str, object]:
    """Return joined incident records suitable for filtering and prioritization."""

    return {
        "mode": "mock",
        "verification": "LOCAL MOCK VERIFIED",
        "items": portfolio_items(repository),
    }


@app.get("/api/v1/integrations/health")
async def integration_health_endpoint() -> dict[str, object]:
    """Expose boundary readiness without leaking credentials or implying live calls."""

    readiness = configuration_readiness()
    sap_configured = all(readiness.values())
    sap_live_verified = _env_flag("SAP_AI_LIVE_VERIFIED")
    live_ai_requests_enabled = _live_ai_requests_enabled()
    state_persistence = _state_persistence_scope()
    return {
        "mode": "mock",
        "checked_at": repository.demo_now.isoformat(),
        "components": [
            {
                "component_id": "decision-engine",
                "name": "Deterministic decision engine",
                "category": "Core service",
                "status": "OPERATIONAL",
                "detail": "Hourly simulation and bounded scenario evaluation are available.",
                "live": True,
            },
            {
                "component_id": "state-store",
                "name": "Operational state store",
                "category": "Data layer",
                "status": "OPERATIONAL",
                "detail": (
                    f"Validated mutable state uses {repository.storage_name} "
                    f"with {state_persistence} persistence scope."
                ),
                "live": state_persistence in {"durable-local", "durable-cloud"},
            },
            {
                "component_id": "sap-ai",
                "name": "SAP AI Core explanation",
                "category": "Decision augmentation",
                "status": (
                    "OPERATIONAL"
                    if sap_live_verified and live_ai_requests_enabled
                    else "VERIFIED"
                    if sap_live_verified
                    else "READY"
                    if sap_configured
                    else "NOT_CONFIGURED"
                ),
                "detail": (
                    "A controlled live inference completed successfully; public live requests are disabled by policy."
                    if sap_live_verified and not live_ai_requests_enabled
                    else "A controlled live inference completed successfully; deterministic fallback remains available."
                    if sap_live_verified
                    else "Credential fields are present; no verified live call is recorded for this runtime."
                    if sap_configured
                    else "Optional credential fields are incomplete; deterministic fallback remains active."
                ),
                "live": sap_live_verified and live_ai_requests_enabled,
            },
            {
                "component_id": "aws-events",
                "name": "AWS disruption events",
                "category": "Event ingestion",
                "status": "EMULATED",
                "detail": "The event contract is exercised locally; no live AWS call has been performed.",
                "live": False,
            },
            {
                "component_id": "sap-erp",
                "name": "SAP ERP transaction writeback",
                "category": "Execution boundary",
                "status": "DISABLED",
                "detail": "Approval changes local simulated state only; external posting is intentionally blocked.",
                "live": False,
            },
        ],
    }


@app.get("/api/v1/inventory")
async def list_inventory_endpoint() -> dict[str, object]:
    return {
        "mode": "mock",
        "verification": "LOCAL MOCK VERIFIED",
        "items": [item.model_dump(mode="json") for item in inventory_views(repository)],
    }


@app.get("/api/v1/shipments")
async def list_shipments_endpoint() -> dict[str, object]:
    return {
        "mode": "mock",
        "verification": "LOCAL MOCK VERIFIED",
        "shipments": [
            item.model_dump(mode="json") for item in repository.list_shipments()
        ],
    }


@app.get("/api/v1/incidents")
async def list_incidents_endpoint() -> dict[str, object]:
    return {
        "mode": "mock",
        "incidents": [
            item.model_dump(mode="json") for item in repository.list_incidents()
        ],
    }


@app.get("/api/v1/incidents/{incident_id}")
async def get_incident_endpoint(incident_id: str) -> dict[str, object]:
    return {
        "mode": "mock",
        "incident": repository.get_incident(incident_id).model_dump(mode="json"),
    }


@app.post("/api/v1/incidents", status_code=status.HTTP_201_CREATED)
async def create_incident_endpoint(payload: IncidentCreateRequest) -> JSONResponse:
    incident, created = ingest_incident(repository, payload)
    body = {
        "mode": "mock",
        "created": created,
        "incident": incident.model_dump(mode="json"),
    }
    return JSONResponse(
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        content=jsonable_encoder(body),
    )


@app.post("/api/v1/analysis/disruption")
async def disruption_analysis(payload: DisruptionAnalysisRequest) -> dict[str, object]:
    """Analyze a seeded incident or the original Phase-1 compatibility request."""

    if payload.incident_id:
        live_ai_requests_enabled = _live_ai_requests_enabled()
        analysis = run_bounded_orchestration(
            repository,
            incident_id=payload.incident_id,
            target_downtime_hours=payload.target_downtime_hours,
            use_live_ai=payload.use_live_ai and live_ai_requests_enabled,
        )
        return {
            "mode": analysis.mode.value,
            "verification": (
                "LIVE AI + LOCAL ENGINE"
                if analysis.mode.value == "live_ai"
                else "LOCAL MOCK VERIFIED"
            ),
            "live_ai": {
                "requested": payload.use_live_ai,
                "runtime_enabled": live_ai_requests_enabled,
            },
            "analysis": analysis.model_dump(mode="json"),
        }

    # Compatibility boundary for consumers built against the initial prototype.
    assert payload.material_id is not None
    assert payload.facility_id is not None
    assert payload.delay_days is not None
    item = get_legacy_inventory_item(payload.material_id, payload.facility_id)
    if item is None:
        raise EntityNotFoundError(
            "Inventory item not found for "
            f"material={payload.material_id} facility={payload.facility_id}"
        )
    shipment = get_legacy_shipment(payload.material_id, payload.facility_id)
    if shipment is None:
        raise EntityNotFoundError(
            "Shipment not found for "
            f"material={payload.material_id} facility={payload.facility_id}"
        )
    analysis = project_disruption(
        item,
        baseline_arrival_day=shipment.scheduled_arrival_day,
        inbound_quantity=shipment.quantity,
        delay_days=payload.delay_days,
    )
    return {
        "mode": "mock",
        "verification": "LEGACY LOCAL MOCK VERIFIED",
        "analysis": analysis.__dict__,
    }


@app.post("/api/v1/scenarios/compare")
async def compare_scenarios(payload: ScenarioCompareRequest) -> dict[str, object]:
    analysis = run_deterministic_analysis(
        repository,
        incident_id=payload.incident_id,
        target_downtime_hours=payload.target_downtime_hours,
    )
    return {
        "mode": analysis.mode.value,
        "analysis_id": analysis.analysis_id,
        "baseline": analysis.baseline.model_dump(mode="json"),
        "scenarios": [item.model_dump(mode="json") for item in analysis.scenarios],
        "recommended_scenario_id": analysis.recommended_scenario_id,
        "recommendation_rationale": analysis.recommendation_rationale,
    }


@app.get("/api/v1/analyses/latest")
async def latest_analysis_endpoint(
    incident_id: str = Query(min_length=1),
) -> dict[str, object]:
    """Return resumable analysis state without creating new audit activity."""

    analysis = repository.latest_analysis_for_incident(incident_id)
    return {
        "mode": "mock",
        "analysis": analysis.model_dump(mode="json") if analysis else None,
    }


@app.get("/api/v1/analyses/{analysis_id}")
async def get_analysis_endpoint(analysis_id: str) -> dict[str, object]:
    """Return one persisted analysis for scenario deep links."""

    analysis = repository.get_analysis(analysis_id)
    return {
        "mode": analysis.mode.value,
        "analysis": analysis.model_dump(mode="json"),
    }


@app.post("/api/v1/transaction-drafts", status_code=status.HTTP_201_CREATED)
async def create_transaction_draft_endpoint(
    payload: TransactionDraftCreateRequest,
) -> dict[str, object]:
    draft = create_transaction_draft(repository, payload)
    return {
        "mode": "mock",
        "message": "Simulated draft created; no SAP transaction was executed.",
        "draft": draft.model_dump(mode="json"),
    }


@app.get("/api/v1/transaction-drafts")
async def list_transaction_drafts_endpoint(
    incident_id: str | None = Query(default=None),
) -> dict[str, object]:
    drafts = repository.list_drafts()
    if incident_id:
        drafts = [item for item in drafts if item.incident_id == incident_id]
    return {"mode": "mock", "drafts": [item.model_dump(mode="json") for item in drafts]}


@app.post("/api/v1/transaction-drafts/{draft_id}/decision")
async def decide_transaction_draft_endpoint(
    draft_id: str,
    payload: TransactionDecisionRequest,
) -> dict[str, object]:
    draft = decide_transaction_draft(repository, draft_id=draft_id, request=payload)
    return {
        "mode": "mock",
        "message": (
            f"Simulated draft marked {draft.status.value}; no SAP transaction was executed."
        ),
        "draft": draft.model_dump(mode="json"),
    }


@app.get("/api/v1/audit")
async def list_audit_endpoint(
    incident_id: str | None = Query(default=None),
) -> dict[str, object]:
    records = repository.list_audit(incident_id=incident_id)
    return {"mode": "mock", "records": [item.model_dump(mode="json") for item in records]}


@app.post("/api/v1/demo/reset")
async def reset_demo_endpoint() -> dict[str, object]:
    repository.reset()
    return {
        "status": "reset",
        "mode": "mock",
        "demo_now": repository.demo_now.isoformat(),
        "message": "Synthetic fixtures restored and mutable demo state cleared.",
    }
