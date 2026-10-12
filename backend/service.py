"""Application services joining repository, deterministic engine, and approvals."""

from __future__ import annotations

from datetime import datetime

from agent.security import sanitize_untrusted_text
from backend.inventory import inventory_risk_level
from backend.optimization import evaluate_mitigations
from backend.repository import DEMO_TIMEZONE, EntityNotFoundError, InMemoryRepository
from backend.schemas import (
    AnalysisResult,
    DecisionAction,
    DraftAction,
    DraftStatus,
    Incident,
    IncidentCreateRequest,
    InventoryView,
    OperationMode,
    ScenarioResult,
    TransactionDecisionRequest,
    TransactionDraft,
    TransactionDraftCreateRequest,
)

DEMO_APPROVAL_THRESHOLD_IDR = 50_000_000
DEMO_APPROVAL_POLICY = (
    "Demo policy: manager approval is required above IDR 50,000,000 and for all "
    "modeled stock transfers. Approval changes local simulated state only."
)


class InvalidStateTransitionError(ValueError):
    """Raised when a draft decision violates the local state machine."""


class InfeasibleDraftError(ValueError):
    """Raised when a transaction draft cannot be grounded in an analysis."""


def inventory_views(repo: InMemoryRepository) -> list[InventoryView]:
    """Return non-secret inventory views with explicit derived quantities."""

    return [
        InventoryView(
            material_id=item.material_id,
            material_name=item.material_name,
            facility_id=item.facility_id,
            facility_name=item.facility_name,
            on_hand=item.on_hand,
            reserved=item.reserved,
            unavailable=item.unavailable,
            usable_quantity=item.usable_quantity,
            hourly_demand=item.hourly_demand,
            hours_of_cover=(
                round(item.hours_of_cover, 4)
                if item.hours_of_cover is not None
                else None
            ),
            safety_stock=item.safety_stock,
            unit=item.unit,
            risk_level=inventory_risk_level(item),
        )
        for item in repo.list_inventory()
    ]


def ingest_incident(
    repo: InMemoryRepository,
    request: IncidentCreateRequest,
) -> tuple[Incident, bool]:
    """Validate referenced entities and ingest an event idempotently."""

    repo.get_shipment(request.shipment_id)
    title, title_warning = sanitize_untrusted_text(request.title, max_length=160)
    description, description_warning = sanitize_untrusted_text(request.description)
    incident = Incident(
        **request.model_dump(exclude={"title", "description"}),
        title=title,
        description=description,
        injection_warning=title_warning or description_warning,
    )
    return repo.upsert_incident(incident)


def run_deterministic_analysis(
    repo: InMemoryRepository,
    *,
    incident_id: str,
    target_downtime_hours: float = 0,
    persist: bool = True,
) -> AnalysisResult:
    """Run a reproducible incident-to-recommendation analysis."""

    incident = repo.get_incident(incident_id)
    shipment = repo.get_shipment(incident.shipment_id)
    record = repo.get_inventory(
        shipment.material_id,
        shipment.destination_facility_id,
    )
    options = []
    for option in repo.options_for_incident(incident_id):
        if option.option_type != "TRANSFER":
            options.append(option)
            continue
        source = repo.find_inventory(option.material_id, option.source_id)
        if source is None or source.unit != option.unit:
            options.append(option.model_copy(update={"available": False}))
            continue
        # A scenario may reserve at most the source's usable position. This is a
        # hypothetical allocation only; repository stock is never mutated while
        # alternative scenarios are compared.
        options.append(
            option.model_copy(
                update={
                    "available_quantity": min(
                        option.available_quantity, source.usable_quantity
                    )
                }
            )
        )
    baseline, scenarios, recommended = evaluate_mitigations(
        record=record,
        shipment=shipment,
        incident=incident,
        options=options,
        start_at=repo.demo_now,
        target_downtime_hours=target_downtime_hours,
    )

    if recommended.feasible:
        rationale = (
            f"{recommended.scenario_id} satisfies the modeled downtime target with "
            f"{recommended.simulation.downtime_hours:.1f}h downtime and total modeled "
            f"cost IDR {recommended.cost_breakdown.total_idr:,.0f}."
        )
    else:
        rationale = (
            f"No scenario fully satisfies the modeled downtime target. "
            f"{recommended.scenario_id} is damage limitation with "
            f"{recommended.simulation.downtime_hours:.1f}h residual downtime."
        )

    draft_type = _draft_type(recommended)
    estimated_cost = recommended.cost_breakdown.logistics_and_purchase_idr
    requires_approval = (
        estimated_cost > DEMO_APPROVAL_THRESHOLD_IDR
        or any(item.option_type == "TRANSFER" for item in recommended.allocations)
    )
    warnings = [
        "Synthetic ERP and logistics assumptions; no live SAP transaction is executed.",
        "AWS event flow is locally emulated unless separately marked live verified.",
    ]
    if not recommended.feasible:
        warnings.append("Every evaluated option leaves residual production impact.")
    if incident.injection_warning:
        warnings.append("Untrusted instruction-like event text was removed before analysis.")

    evidence_ids = [incident.incident_id, shipment.shipment_id]
    evidence_ids.extend(item.option_id for item in recommended.allocations)
    analysis = AnalysisResult(
        incident_id=incident.incident_id,
        analysis_id=f"ANL-{incident.incident_id}-{int(target_downtime_hours)}",
        mode=OperationMode.MOCK,
        generated_at=repo.demo_now,
        input_assumptions={
            "time_zone": "Asia/Makassar (UTC+08:00)",
            "currency": "IDR",
            "quantity_unit": record.unit,
            "hourly_demand": record.hourly_demand,
            "starting_usable_quantity": record.usable_quantity,
            "safety_stock": record.safety_stock,
            "downtime_cost_per_hour_idr": record.downtime_cost_per_hour_idr,
            "target_downtime_hours": target_downtime_hours,
            "objective": "meet downtime target, then minimize downtime and total cost",
        },
        affected_material={"id": record.material_id, "name": record.material_name},
        facility={"id": record.facility_id, "name": record.facility_name},
        stockout_at=baseline.simulation.stockout_at,
        hours_of_cover=(
            round(record.hours_of_cover, 4)
            if record.hours_of_cover is not None
            else None
        ),
        shortage_quantity_by_time=baseline.simulation.shortage_quantity_by_time,
        baseline=baseline,
        scenarios=scenarios,
        recommended_scenario_id=recommended.scenario_id,
        recommendation_rationale=rationale,
        evidence_ids=evidence_ids,
        draft_action=DraftAction(
            draft_type=draft_type,
            summary=_draft_summary(recommended),
            estimated_cost_idr=estimated_cost,
        ),
        requires_approval=requires_approval,
        warnings=warnings,
    )
    if persist:
        repo.save_analysis(analysis)
    return analysis


def create_transaction_draft(
    repo: InMemoryRepository,
    request: TransactionDraftCreateRequest,
) -> TransactionDraft:
    """Create and submit a local reviewable draft; never call a live ERP API."""

    existing = repo.find_draft_by_idempotency_key(request.idempotency_key)
    if existing is not None:
        return existing

    analysis = repo.get_analysis(request.analysis_id)
    if analysis.incident_id != request.incident_id:
        raise InfeasibleDraftError("analysis does not belong to the requested incident")
    scenario = _find_scenario(analysis, request.scenario_id)
    if not scenario.allocations:
        raise InfeasibleDraftError("baseline/wait scenario does not create a transaction")

    draft_type = _draft_type(scenario)
    if draft_type == "NONE":
        raise InfeasibleDraftError("selected scenario has no draftable action")

    cost = scenario.cost_breakdown.logistics_and_purchase_idr
    requires_approval = (
        cost > DEMO_APPROVAL_THRESHOLD_IDR
        or any(item.option_type == "TRANSFER" for item in scenario.allocations)
    )
    draft = TransactionDraft(
        draft_id=repo.next_draft_id(),
        incident_id=request.incident_id,
        analysis_id=request.analysis_id,
        scenario_id=request.scenario_id,
        draft_type=draft_type,
        status=DraftStatus.DRAFT,
        material_id=analysis.affected_material["id"],
        destination_facility_id=analysis.facility["id"],
        allocations=scenario.allocations,
        estimated_cost_idr=cost,
        created_at=datetime.now(DEMO_TIMEZONE),
        requested_by=request.requested_by,
        idempotency_key=request.idempotency_key,
        version=1,
        requires_approval=requires_approval,
        approval_policy=DEMO_APPROVAL_POLICY,
    )
    draft = draft.model_copy(update={"status": DraftStatus.PENDING_APPROVAL})
    draft, created = repo.save_draft_if_idempotency_absent(draft)
    if not created:
        return draft
    repo.record_audit(
        action="DRAFT_CREATED",
        actor=request.requested_by,
        entity_type="transaction_draft",
        entity_id=draft.draft_id,
        incident_id=draft.incident_id,
        summary=f"Created simulated {draft.draft_type} draft",
    )
    repo.record_audit(
        action="DRAFT_SUBMITTED",
        actor=request.requested_by,
        entity_type="transaction_draft",
        entity_id=draft.draft_id,
        incident_id=draft.incident_id,
        summary="Draft submitted for human approval",
    )
    return draft


def decide_transaction_draft(
    repo: InMemoryRepository,
    *,
    draft_id: str,
    request: TransactionDecisionRequest,
) -> TransactionDraft:
    """Apply a valid local approval/rejection transition and record the audit."""

    draft = repo.get_draft(draft_id)
    if request.actor.strip().casefold() == draft.requested_by.strip().casefold():
        raise InvalidStateTransitionError(
            "the approver must be different from the requesting operator"
        )
    if request.expected_version is not None and request.expected_version != draft.version:
        raise InvalidStateTransitionError(
            f"draft {draft_id} changed from version {request.expected_version} "
            f"to {draft.version}; refresh before deciding"
        )
    if draft.status != DraftStatus.PENDING_APPROVAL:
        raise InvalidStateTransitionError(
            f"draft {draft_id} is {draft.status.value}; only PENDING_APPROVAL can be decided"
        )
    status = (
        DraftStatus.APPROVED
        if request.action == DecisionAction.APPROVE
        else DraftStatus.REJECTED
    )
    decided = draft.model_copy(
        update={
            "status": status,
            "decision_actor": request.actor,
            "decision_at": datetime.now(DEMO_TIMEZONE),
            "decision_reason": request.justification,
            "version": draft.version + 1,
        }
    )
    if not repo.save_draft_if_current(
        decided,
        expected_version=draft.version,
        expected_status=DraftStatus.PENDING_APPROVAL,
    ):
        raise InvalidStateTransitionError(
            f"draft {draft_id} changed while the decision was being submitted; refresh and retry"
        )
    repo.record_audit(
        action=f"DRAFT_{status.value}",
        actor=request.actor,
        entity_type="transaction_draft",
        entity_id=draft_id,
        incident_id=draft.incident_id,
        summary=(
            f"Simulated draft {status.value.lower()}; no SAP transaction executed"
        ),
    )
    return decided


def _find_scenario(analysis: AnalysisResult, scenario_id: str) -> ScenarioResult:
    candidates = [analysis.baseline, *analysis.scenarios]
    for scenario in candidates:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise EntityNotFoundError(f"Scenario not found in analysis: {scenario_id}")


def _draft_type(scenario: ScenarioResult) -> str:
    kinds = {item.option_type for item in scenario.allocations}
    if not kinds:
        return "NONE"
    if kinds == {"TRANSFER"}:
        return "STOCK_TRANSFER"
    if kinds <= {"PURCHASE", "EXPEDITE"}:
        return "PURCHASE_ORDER"
    return "COMBINED"


def _draft_summary(scenario: ScenarioResult) -> str:
    if not scenario.allocations:
        return "No transaction draft is produced for the wait scenario."
    parts = [
        f"{item.option_type} {item.quantity:g} {item.unit} from {item.source_name}"
        for item in scenario.allocations
    ]
    return "; ".join(parts)
