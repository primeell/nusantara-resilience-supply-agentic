"""In-memory ERP adapter used for local development and tests."""

from __future__ import annotations

from dataclasses import dataclass

from backend.inventory import InventoryItem


@dataclass(frozen=True)
class Shipment:
    """Deterministic inbound shipment context for disruption analysis."""

    shipment_id: str
    material_id: str
    facility_id: str
    origin_port: str
    destination_port: str
    scheduled_arrival_day: int
    quantity: int


def list_inventory() -> list[InventoryItem]:
    """Return deterministic mock inventory data without external dependencies."""

    return [
        InventoryItem("MAT-001", "ID-JKT-01", 420, 60, 8),
        InventoryItem("MAT-002", "ID-SBY-01", 1000, 40, 12),
    ]


def list_shipments() -> list[Shipment]:
    """Return deterministic shipment context used by disruption analysis."""

    return [
        Shipment("SHP-001", "MAT-001", "ID-JKT-01", "SG-SIN", "ID-JKT", 8, 600),
        Shipment("SHP-002", "MAT-002", "ID-SBY-01", "MY-TPP", "ID-SBY", 12, 480),
    ]


def get_inventory_item(material_id: str, facility_id: str) -> InventoryItem | None:
    """Return one inventory item by composite key."""

    return next(
        (
            item
            for item in list_inventory()
            if item.material_id == material_id and item.facility_id == facility_id
        ),
        None,
    )


def get_shipment(material_id: str, facility_id: str) -> Shipment | None:
    """Return the matching deterministic shipment context."""

    return next(
        (
            shipment
            for shipment in list_shipments()
            if shipment.material_id == material_id and shipment.facility_id == facility_id
        ),
        None,
    )
