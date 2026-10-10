"""SAP business-data adapter boundary for future BTP integration."""

from __future__ import annotations

from typing import Any


def to_sap_material_payload(material_id: str, quantity: int) -> dict[str, Any]:
    """Build a minimal, side-effect-free material payload."""

    if quantity < 0:
        raise ValueError("quantity must not be negative")
    return {"materialId": material_id, "quantity": quantity}

