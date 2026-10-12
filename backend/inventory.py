"""Inventory domain and deterministic projection logic for the MVP backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.schemas import (
    Arrival,
    InventoryProjectionPoint,
    InventoryRecord,
    InventorySimulation,
    ShortagePoint,
)


@dataclass(frozen=True)
class InventoryItem:
    """Inventory position for one material at one facility."""

    material_id: str
    facility_id: str
    on_hand: int
    daily_demand: int
    lead_time_days: int

    @property
    def days_of_cover(self) -> float:
        """Return stock coverage in days, or infinity when demand is not positive."""

        return self.on_hand / self.daily_demand if self.daily_demand > 0 else float("inf")


@dataclass(frozen=True)
class InventoryProjection:
    """Deterministic disruption projection for one inventory and shipment path."""

    material_id: str
    facility_id: str
    delay_days: int
    baseline_arrival_day: int
    delayed_arrival_day: int
    projected_stockout_day: int | None
    projected_stockout_hours: int | None
    unmet_demand_units: int
    downtime_days: int
    baseline_risk: str
    disrupted_risk: str


def stockout_risk(item: InventoryItem, *, safety_days: int = 7) -> str:
    """Classify stockout risk using a transparent days-of-cover rule."""

    if item.days_of_cover < item.lead_time_days:
        return "high"
    if item.days_of_cover < item.lead_time_days + safety_days:
        return "medium"
    return "low"


def project_disruption(
    item: InventoryItem,
    *,
    baseline_arrival_day: int,
    inbound_quantity: int,
    delay_days: int,
) -> InventoryProjection:
    """Project a delayed inbound shipment with a simple deterministic daily model."""

    if delay_days < 0:
        raise ValueError("delay_days must be >= 0")
    if baseline_arrival_day < 0:
        raise ValueError("baseline_arrival_day must be >= 0")
    if inbound_quantity < 0:
        raise ValueError("inbound_quantity must be >= 0")

    delayed_arrival_day = baseline_arrival_day + delay_days
    inventory_position = item.on_hand
    projected_stockout_day: int | None = None
    unmet_demand_units = 0
    downtime_days = 0

    for day in range(1, delayed_arrival_day + 1):
        # Arrival-day rule: the delayed inbound is received at the start of the
        # delayed arrival day, before that day's demand is consumed.
        if day == delayed_arrival_day:
            inventory_position += inbound_quantity

        demand = item.daily_demand
        fulfilled = min(max(inventory_position, 0), demand)
        inventory_position -= demand
        unmet_today = demand - fulfilled

        if unmet_today > 0:
            unmet_demand_units += unmet_today
            downtime_days += 1
            if projected_stockout_day is None:
                projected_stockout_day = day

    projected_stockout_hours = (
        projected_stockout_day * 24 if projected_stockout_day is not None else None
    )

    return InventoryProjection(
        material_id=item.material_id,
        facility_id=item.facility_id,
        delay_days=delay_days,
        baseline_arrival_day=baseline_arrival_day,
        delayed_arrival_day=delayed_arrival_day,
        projected_stockout_day=projected_stockout_day,
        projected_stockout_hours=projected_stockout_hours,
        unmet_demand_units=unmet_demand_units,
        downtime_days=downtime_days,
        baseline_risk=stockout_risk(item),
        disrupted_risk="high" if projected_stockout_day is not None else stockout_risk(item),
    )


def calculate_usable_inventory(
    on_hand: float,
    reserved: float,
    unavailable: float,
) -> float:
    """Calculate inventory that can actually be consumed or transferred."""

    values = (on_hand, reserved, unavailable)
    if any(value < 0 for value in values):
        raise ValueError("inventory quantities must be >= 0")
    return max(0.0, on_hand - reserved - unavailable)


def inventory_risk_level(record: InventoryRecord) -> str:
    """Classify operational risk without conflating safety stock and outage."""

    usable = record.usable_quantity
    if usable <= 0:
        return "critical"
    if usable <= record.safety_stock:
        return "warning"
    return "normal"


def simulate_time_phased_inventory(
    record: InventoryRecord,
    *,
    start_at: datetime,
    horizon_hours: int,
    arrivals: list[Arrival],
) -> InventorySimulation:
    """Simulate hourly inventory with arrivals applied before demand.

    Downtime is expressed as demand-equivalent hours, so a partial shortage in an
    hour contributes a fractional duration. This keeps the arithmetic explicit
    while preserving a deterministic one-hour simulation resolution.
    """

    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise ValueError("start_at must include a timezone")
    if horizon_hours <= 0:
        raise ValueError("horizon_hours must be > 0")
    if any(arrival.unit != record.unit for arrival in arrivals):
        raise ValueError("arrival units must match inventory unit")
    if any(arrival.arrival_hour >= horizon_hours for arrival in arrivals):
        raise ValueError("arrival must occur within the simulation horizon")

    arrivals_by_hour: dict[int, list[Arrival]] = {}
    for arrival in arrivals:
        arrivals_by_hour.setdefault(arrival.arrival_hour, []).append(arrival)

    quantity = calculate_usable_inventory(
        record.on_hand, record.reserved, record.unavailable
    )
    starting_quantity = quantity
    stockout_at: datetime | None = None
    safety_breach_at: datetime | None = None
    recovery_at: datetime | None = None
    downtime_hours = 0.0
    unmet_demand = 0.0
    shortage_points: list[ShortagePoint] = []
    projection_points = [
        InventoryProjectionPoint(
            hour=0,
            timestamp=start_at,
            quantity=round(quantity, 6),
            arrival_quantity=0,
            unmet_demand=0,
            unit=record.unit,
        )
    ]
    shortage_active = False

    if quantity <= record.safety_stock:
        safety_breach_at = start_at

    for hour in range(horizon_hours):
        hour_arrivals = arrivals_by_hour.get(hour, [])
        arrival_quantity = sum(item.quantity for item in hour_arrivals)
        if hour_arrivals:
            quantity += arrival_quantity
            if shortage_active and quantity >= record.hourly_demand:
                recovery_at = recovery_at or start_at + timedelta(hours=hour)
                shortage_active = False

        demand = record.hourly_demand
        if demand <= 0:
            projection_points.append(
                InventoryProjectionPoint(
                    hour=hour + 1,
                    timestamp=start_at + timedelta(hours=hour + 1),
                    quantity=round(quantity, 6),
                    arrival_quantity=round(arrival_quantity, 6),
                    unmet_demand=0,
                    unit=record.unit,
                )
            )
            continue

        quantity_before = quantity
        fulfilled = min(quantity_before, demand)
        unmet = demand - fulfilled
        quantity = max(0.0, quantity_before - demand)

        if safety_breach_at is None and quantity < record.safety_stock:
            crossing_fraction = max(
                0.0,
                min(1.0, (quantity_before - record.safety_stock) / demand),
            )
            safety_breach_at = start_at + timedelta(hours=hour + crossing_fraction)

        if unmet > 0:
            if stockout_at is None:
                available_fraction = quantity_before / demand
                stockout_at = start_at + timedelta(hours=hour + available_fraction)
            shortage_active = True
            unmet_demand += unmet
            downtime_hours += unmet / demand
            shortage_points.append(
                ShortagePoint(hour=hour + 1, unmet_quantity=round(unmet, 6), unit=record.unit)
            )

        projection_points.append(
            InventoryProjectionPoint(
                hour=hour + 1,
                timestamp=start_at + timedelta(hours=hour + 1),
                quantity=round(quantity, 6),
                arrival_quantity=round(arrival_quantity, 6),
                unmet_demand=round(unmet, 6),
                unit=record.unit,
            )
        )

    return InventorySimulation(
        start_at=start_at,
        horizon_hours=horizon_hours,
        starting_usable_quantity=round(starting_quantity, 6),
        hourly_demand=record.hourly_demand,
        safety_stock=record.safety_stock,
        stockout_at=stockout_at,
        safety_breach_at=safety_breach_at,
        recovery_at=recovery_at,
        downtime_hours=round(downtime_hours, 6),
        unmet_demand=round(unmet_demand, 6),
        ending_quantity=round(quantity, 6),
        unit=record.unit,
        shortage_quantity_by_time=shortage_points,
        inventory_by_time=projection_points,
    )
