"""Typed API and domain contracts for the NSRA MVP."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base model that rejects accidental contract drift."""

    model_config = ConfigDict(extra="forbid")


class OperationMode(str, Enum):
    MOCK = "mock"
    LIVE_AI = "live_ai"
    FALLBACK = "fallback"


class DraftStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DecisionAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class Material(StrictModel):
    material_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)


class InventoryRecord(StrictModel):
    material_id: str
    material_name: str
    facility_id: str
    facility_name: str
    on_hand: float = Field(ge=0)
    reserved: float = Field(ge=0)
    unavailable: float = Field(ge=0)
    hourly_demand: float = Field(ge=0)
    safety_stock: float = Field(ge=0)
    unit: str
    downtime_cost_per_hour_idr: float = Field(ge=0)

    @property
    def usable_quantity(self) -> float:
        return max(0.0, self.on_hand - self.reserved - self.unavailable)

    @property
    def hours_of_cover(self) -> float | None:
        return (
            self.usable_quantity / self.hourly_demand
            if self.hourly_demand > 0
            else None
        )


class InventoryView(StrictModel):
    material_id: str
    material_name: str
    facility_id: str
    facility_name: str
    on_hand: float
    reserved: float
    unavailable: float
    usable_quantity: float
    hourly_demand: float
    hours_of_cover: float | None
    safety_stock: float
    unit: str
    risk_level: Literal["normal", "warning", "critical"]


class Shipment(StrictModel):
    shipment_id: str
    purchase_order_id: str
    material_id: str
    origin: str
    destination_facility_id: str
    quantity: float = Field(gt=0)
    unit: str
    baseline_eta: datetime
    current_eta: datetime
    status: str

    @field_validator("baseline_eta", "current_eta")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value


class Incident(StrictModel):
    incident_id: str
    source: str
    event_type: str
    severity: Literal["INFO", "MEDIUM", "HIGH", "CRITICAL"]
    title: str
    description: str
    shipment_id: str
    detected_at: datetime
    delay_hours: int = Field(ge=0)
    injection_warning: bool = False

    @field_validator("detected_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("detected_at must include a timezone")
        return value


class IncidentCreateRequest(StrictModel):
    incident_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    severity: Literal["INFO", "MEDIUM", "HIGH", "CRITICAL"]
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    shipment_id: str = Field(min_length=1)
    detected_at: datetime
    delay_hours: int = Field(ge=0, le=24 * 30)

    @field_validator("detected_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("detected_at must include a timezone")
        return value


class IncidentCreateResponse(StrictModel):
    incident: Incident
    created: bool
    mode: OperationMode = OperationMode.MOCK


class MitigationOption(StrictModel):
    option_id: str
    incident_id: str
    name: str
    option_type: Literal["EXPEDITE", "TRANSFER", "PURCHASE"]
    material_id: str
    destination_facility_id: str
    source_id: str
    source_name: str
    transport_mode: str
    available_quantity: float = Field(ge=0)
    unit: str
    dispatch_delay_hours: int = Field(ge=0)
    travel_time_hours: int = Field(ge=0)
    arrival_hours: int = Field(ge=0)
    dispatch_cutoff_at: datetime | None = None
    fixed_cost_idr: float = Field(ge=0)
    variable_cost_per_unit_idr: float = Field(ge=0)
    minimum_order_quantity: float = Field(ge=0)
    reliability: float = Field(ge=0, le=1)
    available: bool

    @field_validator("dispatch_cutoff_at")
    @classmethod
    def require_cutoff_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("dispatch_cutoff_at must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_lead_time_components(self) -> "MitigationOption":
        expected = self.dispatch_delay_hours + self.travel_time_hours
        if self.arrival_hours != expected:
            raise ValueError(
                "arrival_hours must equal dispatch_delay_hours + travel_time_hours"
            )
        return self


class Arrival(StrictModel):
    evidence_id: str
    arrival_hour: int = Field(ge=0)
    quantity: float = Field(gt=0)
    unit: str


class ShortagePoint(StrictModel):
    hour: int = Field(ge=0)
    unmet_quantity: float = Field(gt=0)
    unit: str


class InventoryProjectionPoint(StrictModel):
    """One auditable hourly point in a scenario inventory projection."""

    hour: int = Field(ge=0)
    timestamp: datetime
    quantity: float = Field(ge=0)
    arrival_quantity: float = Field(ge=0)
    unmet_demand: float = Field(ge=0)
    unit: str

    @field_validator("timestamp")
    @classmethod
    def require_projection_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value


class InventorySimulation(StrictModel):
    start_at: datetime
    horizon_hours: int
    starting_usable_quantity: float
    hourly_demand: float
    safety_stock: float
    stockout_at: datetime | None
    safety_breach_at: datetime | None
    recovery_at: datetime | None
    downtime_hours: float
    unmet_demand: float
    ending_quantity: float
    unit: str
    shortage_quantity_by_time: list[ShortagePoint]
    inventory_by_time: list[InventoryProjectionPoint] = Field(default_factory=list)


class NetworkLocation(StrictModel):
    """Reference location used by the operational network read model."""

    location_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    location_type: Literal["PORT", "FACTORY", "WAREHOUSE", "SUPPLIER"]
    city: str = Field(min_length=1)
    island: str = Field(min_length=1)
    latitude: float = Field(ge=-11.5, le=6.5)
    longitude: float = Field(ge=94.0, le=142.0)


class PortfolioHistoryPoint(StrictModel):
    """Reference historical point, reconciled with current mutable state at read time."""

    observed_at: datetime
    exposure_idr: float = Field(ge=0)
    active_incidents: int = Field(ge=0)
    pending_approvals: int = Field(ge=0)
    approved_actions: int = Field(ge=0)

    @field_validator("observed_at")
    @classmethod
    def require_history_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        return value


class ScenarioAllocation(StrictModel):
    option_id: str
    option_type: str
    source_id: str
    source_name: str
    quantity: float
    unit: str
    arrival_at: datetime
    lead_time_hours: int
    cost_idr: float
    reliability: float


class CostBreakdown(StrictModel):
    logistics_and_purchase_idr: float
    estimated_downtime_idr: float
    total_idr: float
    currency: Literal["IDR"] = "IDR"


class ScenarioResult(StrictModel):
    scenario_id: str
    name: str
    allocations: list[ScenarioAllocation]
    simulation: InventorySimulation
    cost_breakdown: CostBreakdown
    feasible: bool
    constraints_passed: list[str]
    rejected_reasons: list[str]
    risks: list[str]
    rank: int | None = None


class DraftAction(StrictModel):
    draft_type: Literal["STOCK_TRANSFER", "PURCHASE_ORDER", "COMBINED", "NONE"]
    summary: str
    estimated_cost_idr: float = Field(ge=0)


class AgentDecision(StrictModel):
    mode: OperationMode
    recommended_scenario_id: str
    recommendation_rationale: str = Field(min_length=10, max_length=2000)
    evidence_ids: list[str]
    warnings: list[str]
    tool_trace: list[str]


class AnalysisResult(StrictModel):
    incident_id: str
    analysis_id: str
    mode: OperationMode
    generated_at: datetime
    input_assumptions: dict[str, Any]
    affected_material: dict[str, str]
    facility: dict[str, str]
    stockout_at: datetime | None
    hours_of_cover: float | None
    shortage_quantity_by_time: list[ShortagePoint]
    baseline: ScenarioResult
    scenarios: list[ScenarioResult]
    recommended_scenario_id: str
    recommendation_rationale: str
    evidence_ids: list[str]
    draft_action: DraftAction
    requires_approval: bool
    warnings: list[str]
    agent: AgentDecision | None = None


class DisruptionAnalysisRequest(StrictModel):
    incident_id: str | None = None
    material_id: str | None = None
    facility_id: str | None = None
    delay_days: int | None = Field(default=None, ge=0, le=30)
    use_live_ai: bool = False
    target_downtime_hours: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def require_incident_or_legacy_fields(self) -> "DisruptionAnalysisRequest":
        legacy = self.material_id and self.facility_id and self.delay_days is not None
        if not self.incident_id and not legacy:
            raise ValueError(
                "provide incident_id or material_id, facility_id, and delay_days"
            )
        return self


class ScenarioCompareRequest(StrictModel):
    incident_id: str
    target_downtime_hours: float = Field(default=0, ge=0)


class TransactionDraftCreateRequest(StrictModel):
    incident_id: str
    analysis_id: str
    scenario_id: str
    requested_by: str = Field(min_length=1, max_length=120)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class TransactionDraft(StrictModel):
    draft_id: str
    incident_id: str
    analysis_id: str
    scenario_id: str
    draft_type: Literal["STOCK_TRANSFER", "PURCHASE_ORDER", "COMBINED"]
    status: DraftStatus
    material_id: str
    destination_facility_id: str
    allocations: list[ScenarioAllocation]
    estimated_cost_idr: float
    currency: Literal["IDR"] = "IDR"
    created_at: datetime
    requested_by: str
    idempotency_key: str | None = None
    version: int = Field(default=1, ge=1)
    requires_approval: bool
    approval_policy: str
    decision_actor: str | None = None
    decision_at: datetime | None = None
    decision_reason: str | None = None
    simulated_only: Literal[True] = True


class TransactionDecisionRequest(StrictModel):
    action: DecisionAction
    actor: str = Field(min_length=1, max_length=120)
    justification: str = Field(min_length=10, max_length=500)
    expected_version: int | None = Field(default=None, ge=1)


class AuditRecord(StrictModel):
    audit_id: str
    timestamp: datetime
    action: str
    actor: str
    entity_type: str
    entity_id: str
    incident_id: str | None
    summary: str


class ErrorEnvelope(StrictModel):
    error_code: str
    message: str
    details: Any | None = None
    trace_id: str
