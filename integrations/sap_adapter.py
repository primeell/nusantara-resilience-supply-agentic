"""SAP business-data adapter boundary with no live transaction side effects."""

from __future__ import annotations

from typing import Any

from backend.schemas import TransactionDraft


def to_sap_material_payload(material_id: str, quantity: int) -> dict[str, Any]:
    """Build a minimal, side-effect-free material payload."""

    if quantity < 0:
        raise ValueError("quantity must not be negative")
    return {"materialId": material_id, "quantity": quantity}


def to_sap_draft_payload(draft: TransactionDraft) -> dict[str, Any]:
    """Map an approved local draft to a reviewable SAP-shaped payload.

    Building this object is safe: it neither authenticates to SAP nor transmits
    data. The explicit simulation marker prevents the demo from implying a live
    purchase order or stock-transfer posting.
    """

    return {
        "externalReference": draft.draft_id,
        "documentType": draft.draft_type,
        "materialId": draft.material_id,
        "destinationPlant": draft.destination_facility_id,
        "currency": draft.currency,
        "estimatedCost": draft.estimated_cost_idr,
        "approvalStatus": draft.status.value,
        "simulationOnly": True,
        "items": [
            {
                "sourceId": allocation.source_id,
                "optionType": allocation.option_type,
                "quantity": allocation.quantity,
                "unit": allocation.unit,
                "expectedArrival": allocation.arrival_at.isoformat(),
            }
            for allocation in draft.allocations
        ],
    }
