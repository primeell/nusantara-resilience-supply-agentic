"""In-memory ERP adapter used for local development and tests."""

from __future__ import annotations

from backend.inventory import InventoryItem


def list_inventory() -> list[InventoryItem]:
    """Return deterministic mock inventory data without external dependencies."""

    return [
        InventoryItem("MAT-001", "ID-JKT-01", 420, 60, 8),
        InventoryItem("MAT-002", "ID-SBY-01", 1000, 40, 12),
    ]

