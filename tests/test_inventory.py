from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from backend.inventory import (
    InventoryItem,
    calculate_usable_inventory,
    project_disruption,
    simulate_time_phased_inventory,
    stockout_risk,
)
from backend.schemas import Arrival, InventoryRecord


def test_stockout_risk_is_high_when_cover_is_below_lead_time() -> None:
    item = InventoryItem("MAT-1", "FAC-1", on_hand=100, daily_demand=20, lead_time_days=8)
    assert item.days_of_cover == 5
    assert stockout_risk(item) == "high"



def test_stockout_risk_is_low_with_safety_buffer() -> None:
    item = InventoryItem("MAT-2", "FAC-1", on_hand=1000, daily_demand=20, lead_time_days=8)
    assert stockout_risk(item) == "low"



def test_project_disruption_returns_exact_numeric_projection() -> None:
    item = InventoryItem("MAT-001", "ID-JKT-01", on_hand=420, daily_demand=60, lead_time_days=8)

    projection = project_disruption(
        item,
        baseline_arrival_day=8,
        inbound_quantity=600,
        delay_days=4,
    )

    assert projection.baseline_arrival_day == 8
    assert projection.delayed_arrival_day == 12
    assert projection.projected_stockout_day == 8
    assert projection.projected_stockout_hours == 192
    assert projection.unmet_demand_units == 240
    assert projection.downtime_days == 4
    assert projection.baseline_risk == "high"
    assert projection.disrupted_risk == "high"


def _record(**updates: object) -> InventoryRecord:
    values: dict[str, object] = {
        "material_id": "MAT-X",
        "material_name": "Material X",
        "facility_id": "FAC-X",
        "facility_name": "Factory X",
        "on_hand": 100,
        "reserved": 0,
        "unavailable": 0,
        "hourly_demand": 10,
        "safety_stock": 20,
        "unit": "kg",
        "downtime_cost_per_hour_idr": 1_000_000,
    }
    values.update(updates)
    return InventoryRecord.model_validate(values)


def test_usable_inventory_never_goes_below_zero() -> None:
    assert calculate_usable_inventory(100, 60, 60) == 0
    with pytest.raises(ValueError, match="must be >= 0"):
        calculate_usable_inventory(-1, 0, 0)


def test_arrival_exactly_at_stockout_boundary_prevents_outage() -> None:
    start = datetime(2026, 10, 10, 8, tzinfo=ZoneInfo("Asia/Makassar"))
    simulation = simulate_time_phased_inventory(
        _record(),
        start_at=start,
        horizon_hours=20,
        arrivals=[Arrival(evidence_id="SHP-X", arrival_hour=10, quantity=100, unit="kg")],
    )
    assert simulation.stockout_at is None
    assert simulation.downtime_hours == 0
    assert simulation.unmet_demand == 0
    assert simulation.ending_quantity == 0


def test_already_stocked_out_is_reported_at_start() -> None:
    start = datetime(2026, 10, 10, 8, tzinfo=ZoneInfo("Asia/Makassar"))
    simulation = simulate_time_phased_inventory(
        _record(on_hand=50, reserved=50),
        start_at=start,
        horizon_hours=2,
        arrivals=[],
    )
    assert simulation.stockout_at == start
    assert simulation.downtime_hours == 2
    assert simulation.unmet_demand == 20


def test_split_arrivals_recover_inventory_without_double_counting() -> None:
    start = datetime(2026, 10, 10, 8, tzinfo=ZoneInfo("Asia/Makassar"))
    simulation = simulate_time_phased_inventory(
        _record(on_hand=20),
        start_at=start,
        horizon_hours=8,
        arrivals=[
            Arrival(evidence_id="A-1", arrival_hour=3, quantity=20, unit="kg"),
            Arrival(evidence_id="A-2", arrival_hour=5, quantity=40, unit="kg"),
        ],
    )
    assert simulation.unmet_demand == 10
    assert simulation.downtime_hours == 1
    assert simulation.recovery_at == start.replace(hour=11)
    assert simulation.ending_quantity == 10
    assert len(simulation.inventory_by_time) == 9
    assert simulation.inventory_by_time[0].quantity == 20
    assert simulation.inventory_by_time[3].unmet_demand == 10
    assert simulation.inventory_by_time[4].arrival_quantity == 20


def test_wrong_arrival_unit_is_rejected() -> None:
    start = datetime(2026, 10, 10, 8, tzinfo=ZoneInfo("Asia/Makassar"))
    with pytest.raises(ValueError, match="units must match"):
        simulate_time_phased_inventory(
            _record(),
            start_at=start,
            horizon_hours=12,
            arrivals=[Arrival(evidence_id="BAD", arrival_hour=1, quantity=10, unit="ton")],
        )


def test_arrival_at_horizon_boundary_is_not_silently_ignored() -> None:
    start = datetime(2026, 10, 10, 8, tzinfo=ZoneInfo("Asia/Makassar"))
    with pytest.raises(ValueError, match="within the simulation horizon"):
        simulate_time_phased_inventory(
            _record(),
            start_at=start,
            horizon_hours=12,
            arrivals=[
                Arrival(evidence_id="LATE", arrival_hour=12, quantity=10, unit="kg")
            ],
        )
