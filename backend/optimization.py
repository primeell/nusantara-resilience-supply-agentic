"""Placeholder scenario optimization interfaces for the MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations
from math import ceil

from backend.inventory import simulate_time_phased_inventory
from backend.schemas import (
    Arrival,
    CostBreakdown,
    Incident,
    InventoryRecord,
    MitigationOption,
    ScenarioAllocation,
    ScenarioResult,
    Shipment,
)


@dataclass(frozen=True)
class LogisticsScenario:
    """Candidate logistics strategy with an estimated cost and delay."""

    name: str
    cost_usd: float
    delay_days: int


def choose_fastest(scenarios: list[LogisticsScenario]) -> LogisticsScenario | None:
    """Choose the lowest-delay scenario, using cost as a deterministic tie-breaker."""

    return min(scenarios, key=lambda item: (item.delay_days, item.cost_usd), default=None)


def evaluate_mitigations(
    *,
    record: InventoryRecord,
    shipment: Shipment,
    incident: Incident,
    options: list[MitigationOption],
    start_at: datetime,
    target_downtime_hours: float = 0,
) -> tuple[ScenarioResult, list[ScenarioResult], ScenarioResult]:
    """Evaluate bounded mitigation combinations and select a grounded result.

    Objective: prefer scenarios meeting the downtime target, then minimize
    downtime, then total modeled cost. Each candidate remains visible, including
    infeasible options and their rejection reasons.
    """

    if shipment.material_id != record.material_id:
        raise ValueError("shipment material does not match inventory")
    if shipment.destination_facility_id != record.facility_id:
        raise ValueError("shipment destination does not match inventory facility")
    if shipment.unit != record.unit:
        raise ValueError("shipment unit does not match inventory unit")

    delayed_arrival_hour = max(
        0,
        ceil((shipment.current_eta - start_at).total_seconds() / 3600),
    )
    latest_candidate_arrival = max(
        (option.arrival_hours for option in options),
        default=0,
    )
    horizon_hours = max(24, delayed_arrival_hour, latest_candidate_arrival) + 24
    original_arrival = Arrival(
        evidence_id=shipment.shipment_id,
        arrival_hour=delayed_arrival_hour,
        quantity=shipment.quantity,
        unit=shipment.unit,
    )

    baseline_simulation = simulate_time_phased_inventory(
        record,
        start_at=start_at,
        horizon_hours=horizon_hours,
        arrivals=[original_arrival],
    )
    baseline_downtime_cost = (
        baseline_simulation.downtime_hours * record.downtime_cost_per_hour_idr
    )
    baseline_feasible = baseline_simulation.downtime_hours <= target_downtime_hours
    baseline = ScenarioResult(
        scenario_id="BASELINE-WAIT",
        name="Wait for delayed shipment",
        allocations=[],
        simulation=baseline_simulation,
        cost_breakdown=CostBreakdown(
            logistics_and_purchase_idr=0,
            estimated_downtime_idr=round(baseline_downtime_cost, 2),
            total_idr=round(baseline_downtime_cost, 2),
        ),
        feasible=baseline_feasible,
        constraints_passed=["original shipment retained", "no inventory double counting"],
        rejected_reasons=(
            []
            if baseline_feasible
            else [
                f"Modeled downtime {baseline_simulation.downtime_hours:.1f}h exceeds "
                f"target {target_downtime_hours:.1f}h"
            ]
        ),
        risks=(
            []
            if baseline_feasible
            else ["Production demand cannot be fully served before replenishment"]
        ),
    )

    option_groups: list[tuple[MitigationOption, ...]] = [
        (option,) for option in options
    ]
    option_groups.extend(combinations(options, 2))

    results: list[ScenarioResult] = []
    seen_signatures: set[tuple[str, ...]] = set()
    for group in option_groups:
        signature = tuple(sorted(option.option_id for option in group))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        results.append(
            _evaluate_option_group(
                record=record,
                original_arrival=original_arrival,
                options=group,
                start_at=start_at,
                horizon_hours=horizon_hours,
                target_downtime_hours=target_downtime_hours,
            )
        )

    ordered = sorted(
        results,
        key=lambda result: (
            not result.feasible,
            result.simulation.downtime_hours,
            result.cost_breakdown.total_idr,
            result.scenario_id,
        ),
    )
    ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(ordered, 1)]

    candidates = [baseline, *ranked]
    feasible = [item for item in candidates if item.feasible]
    if feasible:
        recommended = min(
            feasible,
            key=lambda item: (
                item.simulation.downtime_hours,
                item.cost_breakdown.total_idr,
            ),
        )
    else:
        recommended = min(
            candidates,
            key=lambda item: (
                item.simulation.downtime_hours,
                item.cost_breakdown.total_idr,
            ),
        )

    return baseline, ranked, recommended


def _evaluate_option_group(
    *,
    record: InventoryRecord,
    original_arrival: Arrival,
    options: tuple[MitigationOption, ...],
    start_at: datetime,
    horizon_hours: int,
    target_downtime_hours: float,
) -> ScenarioResult:
    rejected: list[str] = []
    passed: list[str] = ["original shipment retained", "no cross-scenario stock mutation"]
    risks: list[str] = []
    arrivals = [original_arrival]
    allocations: list[ScenarioAllocation] = []
    action_cost = 0.0

    for option in options:
        if option.material_id != record.material_id:
            rejected.append(
                f"{option.option_id}: material {option.material_id} is incompatible "
                f"with {record.material_id}"
            )
            continue
        if option.destination_facility_id != record.facility_id:
            rejected.append(
                f"{option.option_id}: destination {option.destination_facility_id} "
                f"does not match {record.facility_id}"
            )
            continue
        if not option.available:
            rejected.append(f"{option.option_id}: source is unavailable")
            continue
        if option.unit != record.unit:
            rejected.append(
                f"{option.option_id}: unit {option.unit} is incompatible with {record.unit}"
            )
            continue
        if option.available_quantity <= 0:
            rejected.append(f"{option.option_id}: source capacity is depleted")
            continue
        if option.available_quantity < option.minimum_order_quantity:
            rejected.append(
                f"{option.option_id}: capacity is below minimum order quantity"
            )
            continue
        dispatch_at = start_at + timedelta(hours=option.dispatch_delay_hours)
        if (
            option.dispatch_cutoff_at is not None
            and dispatch_at > option.dispatch_cutoff_at
        ):
            rejected.append(f"{option.option_id}: dispatch misses configured cutoff")
            continue

        quantity = option.available_quantity
        cost = option.fixed_cost_idr + quantity * option.variable_cost_per_unit_idr
        action_cost += cost
        arrivals.append(
            Arrival(
                evidence_id=option.option_id,
                arrival_hour=option.arrival_hours,
                quantity=quantity,
                unit=option.unit,
            )
        )
        allocations.append(
            ScenarioAllocation(
                option_id=option.option_id,
                option_type=option.option_type,
                source_id=option.source_id,
                source_name=option.source_name,
                quantity=quantity,
                unit=option.unit,
                arrival_at=start_at + timedelta(hours=option.arrival_hours),
                lead_time_hours=option.arrival_hours,
                cost_idr=round(cost, 2),
                reliability=option.reliability,
            )
        )
        passed.extend(
            [
                f"{option.option_id}: material and destination compatible",
                f"{option.option_id}: quantity within modeled source capacity",
                (
                    f"{option.option_id}: dispatch {option.dispatch_delay_hours}h + "
                    f"{option.transport_mode} travel {option.travel_time_hours}h"
                ),
            ]
        )
        if option.reliability < 0.9:
            risks.append(
                f"{option.option_id}: modeled reliability is {option.reliability:.0%}"
            )

    simulation = simulate_time_phased_inventory(
        record,
        start_at=start_at,
        horizon_hours=horizon_hours,
        arrivals=arrivals,
    )
    downtime_cost = simulation.downtime_hours * record.downtime_cost_per_hour_idr
    if simulation.downtime_hours > target_downtime_hours:
        rejected.append(
            f"Residual downtime {simulation.downtime_hours:.1f}h exceeds "
            f"target {target_downtime_hours:.1f}h"
        )
    else:
        passed.append("downtime target satisfied")
    if simulation.unmet_demand > 0:
        risks.append(
            f"Residual unmet demand is {simulation.unmet_demand:.1f} {record.unit}"
        )

    feasible = not rejected and simulation.unmet_demand <= 1e-9
    scenario_id = "SCN-" + "+".join(option.option_id for option in options)
    return ScenarioResult(
        scenario_id=scenario_id,
        name=" + ".join(option.name for option in options),
        allocations=allocations,
        simulation=simulation,
        cost_breakdown=CostBreakdown(
            logistics_and_purchase_idr=round(action_cost, 2),
            estimated_downtime_idr=round(downtime_cost, 2),
            total_idr=round(action_cost + downtime_cost, 2),
        ),
        feasible=feasible,
        constraints_passed=passed,
        rejected_reasons=rejected,
        risks=risks,
    )
