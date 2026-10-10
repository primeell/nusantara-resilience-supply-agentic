"""Small inventory-risk interface used by the MVP backend."""

from __future__ import annotations

from dataclasses import dataclass


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
        """Return stock coverage in days, or zero when demand is not positive."""

        return self.on_hand / self.daily_demand if self.daily_demand > 0 else float("inf")


def stockout_risk(item: InventoryItem, *, safety_days: int = 7) -> str:
    """Classify stockout risk using a transparent days-of-cover rule."""

    if item.days_of_cover < item.lead_time_days:
        return "high"
    if item.days_of_cover < item.lead_time_days + safety_days:
        return "medium"
    return "low"

