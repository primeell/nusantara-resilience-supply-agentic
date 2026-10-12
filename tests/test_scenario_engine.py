"""Deterministic optimization and service-level scenario tests."""

from __future__ import annotations

from backend.repository import InMemoryRepository
from backend.service import run_deterministic_analysis


def _scenario(analysis, scenario_id: str):  # type: ignore[no-untyped-def]
    return next(
        item
        for item in [analysis.baseline, *analysis.scenarios]
        if item.scenario_id == scenario_id
    )


def test_four_day_delay_has_exact_grounded_recommendation() -> None:
    repo = InMemoryRepository()
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")

    assert analysis.hours_of_cover == 36
    assert analysis.baseline.simulation.downtime_hours == 60
    assert analysis.baseline.simulation.unmet_demand == 3000
    assert analysis.recommended_scenario_id == "SCN-TRANSFER-MKS+LOCAL-MKS"

    recommended = _scenario(analysis, analysis.recommended_scenario_id)
    assert recommended.feasible is True
    assert recommended.simulation.downtime_hours == 0
    assert recommended.cost_breakdown.logistics_and_purchase_idr == 45_000_000
    assert sum(item.quantity for item in recommended.allocations) == 3000


def test_slower_transfer_does_not_claim_to_prevent_initial_stockout() -> None:
    analysis = run_deterministic_analysis(
        InMemoryRepository(), incident_id="INC-MKS-FOUR-DAY"
    )
    transfer = _scenario(analysis, "SCN-TRANSFER-MKS")

    assert transfer.allocations[0].lead_time_hours == 48
    assert analysis.hours_of_cover == 36
    assert transfer.simulation.stockout_at is not None
    assert transfer.simulation.downtime_hours == 24
    assert transfer.feasible is False


def test_faster_air_freight_is_feasible_but_more_expensive() -> None:
    analysis = run_deterministic_analysis(
        InMemoryRepository(), incident_id="INC-MKS-FOUR-DAY"
    )
    air = _scenario(analysis, "SCN-AIR-MKS")
    mixed = _scenario(analysis, "SCN-TRANSFER-MKS+LOCAL-MKS")

    assert air.feasible is True
    assert air.simulation.downtime_hours == 0
    assert air.cost_breakdown.total_idr == 220_000_000
    assert mixed.cost_breakdown.total_idr == 45_000_000
    assert mixed.rank < air.rank


def test_alternative_scenarios_do_not_mutate_source_inventory() -> None:
    repo = InMemoryRepository()
    before = repo.get_inventory("MAT-CHEM-A", "WH-SBY").usable_quantity
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")
    after = repo.get_inventory("MAT-CHEM-A", "WH-SBY").usable_quantity
    transfer = _scenario(analysis, "SCN-TRANSFER-MKS")

    assert before == after == 1800
    assert transfer.allocations[0].quantity <= before


def test_normal_operation_correctly_keeps_baseline() -> None:
    analysis = run_deterministic_analysis(
        InMemoryRepository(), incident_id="INC-JKT-NORMAL"
    )
    assert analysis.baseline.feasible is True
    assert analysis.baseline.simulation.downtime_hours == 0
    assert analysis.recommended_scenario_id == "BASELINE-WAIT"
    assert analysis.draft_action.draft_type == "NONE"


def test_feasible_wait_competes_with_unnecessary_mitigation() -> None:
    repo = InMemoryRepository()
    template = repo.options[0]
    repo.options.append(
        template.model_copy(
            update={
                "option_id": "UNNECESSARY-JKT",
                "incident_id": "INC-JKT-NORMAL",
                "name": "Unnecessary emergency supply",
                "material_id": "MAT-RESIN-B",
                "destination_facility_id": "FAC-JKT",
                "source_id": "SUP-JKT-X",
                "available_quantity": 1000,
                "unit": "kg",
                "fixed_cost_idr": 100_000_000,
            }
        )
    )
    analysis = run_deterministic_analysis(repo, incident_id="INC-JKT-NORMAL")
    assert analysis.recommended_scenario_id == "BASELINE-WAIT"
    assert analysis.baseline.cost_breakdown.total_idr == 0


def test_unavailable_supplier_is_explicitly_rejected() -> None:
    analysis = run_deterministic_analysis(
        InMemoryRepository(), incident_id="INC-BPN-SUPPLIER-OFFLINE"
    )
    local = _scenario(analysis, "SCN-LOCAL-BPN")
    assert local.feasible is False
    assert local.allocations == []
    assert any("source is unavailable" in reason for reason in local.rejected_reasons)


def test_no_feasible_case_returns_honest_damage_limitation() -> None:
    analysis = run_deterministic_analysis(
        InMemoryRepository(), incident_id="INC-SRG-NO-FEASIBLE"
    )
    selected = _scenario(analysis, analysis.recommended_scenario_id)
    assert selected.feasible is False
    assert selected.simulation.downtime_hours > 0
    assert "No scenario fully satisfies" in analysis.recommendation_rationale
    assert any("residual production impact" in item for item in analysis.warnings)
