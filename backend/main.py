"""FastAPI application for the NSRA local MVP."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.sap_ai_client import configuration_readiness
from backend.inventory import project_disruption, stockout_risk
from backend.mock_erp import get_inventory_item, get_shipment, list_inventory, list_shipments

app = FastAPI(title="Nusantara Supply Resiliency Agent", version="0.1.0")


class DisruptionAnalysisRequest(BaseModel):
    """Request body for deterministic disruption analysis."""

    material_id: str = Field(min_length=1)
    facility_id: str = Field(min_length=1)
    delay_days: int = Field(ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a basic process health response."""

    return {"status": "ok"}


@app.get("/api/v1/status")
def status() -> dict[str, object]:
    """Report non-sensitive local configuration readiness."""

    readiness = configuration_readiness()
    return {
        "application": "nsra",
        "environment": "development",
        "sap": {
            "configured": all(readiness.values()),
            "fields_present": readiness,
        },
        "live_cloud_checks": False,
    }


@app.get("/api/v1/inventory")
def inventory() -> dict[str, object]:
    """Return deterministic mock inventory with derived risk metrics."""

    items = list_inventory()
    return {
        "mode": "MOCK VERIFIED",
        "items": [
            {
                "material_id": item.material_id,
                "facility_id": item.facility_id,
                "on_hand": item.on_hand,
                "daily_demand": item.daily_demand,
                "lead_time_days": item.lead_time_days,
                "days_of_cover": item.days_of_cover,
                "risk_level": stockout_risk(item),
            }
            for item in items
        ],
    }


@app.get("/api/v1/shipments")
def shipments() -> dict[str, object]:
    """Return deterministic mock shipment context."""

    return {
        "mode": "MOCK VERIFIED",
        "shipments": [shipment.__dict__ for shipment in list_shipments()],
    }


@app.post("/api/v1/analysis/disruption")
def disruption_analysis(payload: DisruptionAnalysisRequest) -> dict[str, object]:
    """Run deterministic disruption analysis for a mock material/facility path."""

    item = get_inventory_item(payload.material_id, payload.facility_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Inventory item not found for "
                f"material_id={payload.material_id} facility_id={payload.facility_id}"
            ),
        )

    shipment = get_shipment(payload.material_id, payload.facility_id)
    if shipment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Shipment context not found for "
                f"material_id={payload.material_id} facility_id={payload.facility_id}"
            ),
        )

    analysis = project_disruption(
        item,
        baseline_arrival_day=shipment.scheduled_arrival_day,
        inbound_quantity=shipment.quantity,
        delay_days=payload.delay_days,
    )

    return {
        "mode": "MOCK VERIFIED",
        "analysis": analysis.__dict__,
    }


# Keep this module as the stable Uvicorn entrypoint while the expanded API lives
# in a separate module. Existing commands such as `uvicorn backend.main:app`
# therefore continue to work.
from backend.api import app as app  # noqa: E402,F811
