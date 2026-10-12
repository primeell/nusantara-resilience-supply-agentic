"""Read models for the multi-module NSRA operations control tower.

These functions only aggregate reviewed reference records and current local state.
They never mutate inventory, create analyses, or execute external transactions.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from backend.repository import InMemoryRepository
from backend.schemas import AnalysisResult, DraftStatus, Incident, ScenarioResult
from backend.service import run_deterministic_analysis


SEVERITY_WEIGHT = {"INFO": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
RISK_WEIGHT = {"stable": 0, "watch": 1, "high": 2, "critical": 3}


def _analysis_for_incident(
    repo: InMemoryRepository,
    incident: Incident,
) -> AnalysisResult:
    existing = repo.latest_analysis_for_incident(incident.incident_id)
    if existing is not None:
        return existing
    return run_deterministic_analysis(
        repo,
        incident_id=incident.incident_id,
        persist=False,
    )


def _recommended_scenario(analysis: Any) -> ScenarioResult:
    for scenario in [analysis.baseline, *analysis.scenarios]:
        if scenario.scenario_id == analysis.recommended_scenario_id:
            return scenario
    return analysis.baseline


def portfolio_items(repo: InMemoryRepository) -> list[dict[str, Any]]:
    """Join incidents, logistics, inventory, analysis, and approvals for portfolio use."""

    drafts_by_incident: dict[str, list[Any]] = {}
    for draft in repo.list_drafts():
        drafts_by_incident.setdefault(draft.incident_id, []).append(draft)

    items: list[dict[str, Any]] = []
    for incident in repo.list_incidents():
        shipment = repo.get_shipment(incident.shipment_id)
        inventory = repo.get_inventory(
            shipment.material_id,
            shipment.destination_facility_id,
        )
        analysis = _analysis_for_incident(repo, incident)
        recommended = _recommended_scenario(analysis)
        incident_drafts = sorted(
            drafts_by_incident.get(incident.incident_id, []),
            key=lambda item: item.created_at,
            reverse=True,
        )
        latest_draft = incident_drafts[0] if incident_drafts else None
        is_active = incident.delay_hours > 0 or incident.event_type != "NORMAL_OPERATION"
        approval_status = latest_draft.status.value if latest_draft else "NOT_CREATED"
        items.append(
            {
                "incident_id": incident.incident_id,
                "title": incident.title,
                "description": incident.description,
                "event_type": incident.event_type,
                "severity": incident.severity,
                "detected_at": incident.detected_at,
                "delay_hours": incident.delay_hours,
                "active": is_active,
                "shipment_id": shipment.shipment_id,
                "purchase_order_id": shipment.purchase_order_id,
                "route": f"{shipment.origin} to {inventory.facility_name}",
                "origin": shipment.origin,
                "shipment_status": shipment.status,
                "current_eta": shipment.current_eta,
                "material_id": inventory.material_id,
                "material_name": inventory.material_name,
                "facility_id": inventory.facility_id,
                "facility_name": inventory.facility_name,
                "usable_quantity": inventory.usable_quantity,
                "safety_stock": inventory.safety_stock,
                "hourly_demand": inventory.hourly_demand,
                "hours_of_cover": analysis.hours_of_cover,
                "stockout_at": analysis.stockout_at,
                "baseline_downtime_hours": analysis.baseline.simulation.downtime_hours,
                "recommended_downtime_hours": recommended.simulation.downtime_hours,
                "baseline_exposure_idr": analysis.baseline.cost_breakdown.estimated_downtime_idr,
                "recommended_total_idr": recommended.cost_breakdown.total_idr,
                "recommended_scenario_id": analysis.recommended_scenario_id,
                "analysis_id": analysis.analysis_id if repo.latest_analysis_for_incident(incident.incident_id) else None,
                "analysis_available": repo.latest_analysis_for_incident(incident.incident_id) is not None,
                "approval_status": approval_status,
                "draft_id": latest_draft.draft_id if latest_draft else None,
            }
        )

    return sorted(
        items,
        key=lambda item: (
            not item["active"],
            -SEVERITY_WEIGHT.get(item["severity"], 0),
            item["stockout_at"] or item["current_eta"],
        ),
    )


def risk_matrix(repo: InMemoryRepository, portfolio: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a facility-by-material matrix with textual status in every populated cell."""

    materials = [item.model_dump(mode="json") for item in repo.materials.values()]
    facilities: list[dict[str, str]] = []
    seen_facilities: set[str] = set()
    portfolio_by_pair = {
        (item["facility_id"], item["material_id"]): item for item in portfolio
    }
    cells: list[dict[str, Any]] = []

    for inventory in repo.list_inventory():
        if not inventory.facility_id.startswith("FAC-"):
            continue
        if inventory.facility_id not in seen_facilities:
            facilities.append(
                {"facility_id": inventory.facility_id, "facility_name": inventory.facility_name}
            )
            seen_facilities.add(inventory.facility_id)
        portfolio_item = portfolio_by_pair.get(
            (inventory.facility_id, inventory.material_id)
        )
        severity = portfolio_item["severity"] if portfolio_item else "INFO"
        if portfolio_item and portfolio_item["active"]:
            risk = "critical" if severity == "CRITICAL" else "high" if severity == "HIGH" else "watch"
        else:
            risk = "stable"
        cells.append(
            {
                "facility_id": inventory.facility_id,
                "material_id": inventory.material_id,
                "risk": risk,
                "hours_of_cover": inventory.hours_of_cover,
                "usable_quantity": inventory.usable_quantity,
                "unit": inventory.unit,
            }
        )

    return {"facilities": facilities, "materials": materials, "cells": cells}


def overview_snapshot(repo: InMemoryRepository) -> dict[str, Any]:
    """Return the executive read model with a current-state-reconciled trend."""

    portfolio = portfolio_items(repo)
    active = [item for item in portfolio if item["active"]]
    drafts = repo.list_drafts()
    pending = [item for item in drafts if item.status == DraftStatus.PENDING_APPROVAL]
    approved = [item for item in drafts if item.status == DraftStatus.APPROVED]
    rejected = [item for item in drafts if item.status == DraftStatus.REJECTED]
    exposure = sum(item["baseline_exposure_idr"] for item in active)
    trend = [item.model_dump(mode="json") for item in repo.list_portfolio_history()]
    if trend:
        trend[-1].update(
            {
                "exposure_idr": exposure,
                "active_incidents": len(active),
                "pending_approvals": len(pending),
                "approved_actions": len(approved),
            }
        )

    severity_distribution = Counter(item["severity"] for item in active)
    return {
        "generated_at": repo.demo_now,
        "kpis": {
            "active_incidents": len(active),
            "critical_incidents": severity_distribution.get("CRITICAL", 0),
            "at_risk_facilities": len({item["facility_id"] for item in active}),
            "delayed_routes": sum(1 for item in repo.list_shipments() if item.status == "DELAYED"),
            "baseline_exposure_idr": exposure,
            "pending_approvals": len(pending),
        },
        "severity_distribution": dict(severity_distribution),
        "approval_summary": {
            "pending": len(pending),
            "approved": len(approved),
            "rejected": len(rejected),
            "not_created": sum(1 for item in active if item["approval_status"] == "NOT_CREATED"),
        },
        "trend": trend,
        "risk_matrix": risk_matrix(repo, portfolio),
        "priority_incidents": portfolio[:4],
    }


def network_snapshot(repo: InMemoryRepository) -> dict[str, Any]:
    """Return geographic nodes and auditable shipment/mitigation edges."""

    locations = {item.location_id: item for item in repo.list_locations()}
    by_name = {item.name.casefold(): item for item in locations.values()}
    portfolio = portfolio_items(repo)
    portfolio_by_shipment = {item["shipment_id"]: item for item in portfolio}
    node_risk: dict[str, str] = {key: "stable" for key in locations}
    routes: list[dict[str, Any]] = []

    for shipment in repo.list_shipments():
        source = by_name.get(shipment.origin.casefold())
        destination = locations.get(shipment.destination_facility_id)
        if source is None or destination is None:
            continue
        item = portfolio_by_shipment.get(shipment.shipment_id)
        severity = item["severity"] if item else "INFO"
        route_status = "stable" if shipment.status == "ON_TIME" else (
            "critical" if severity == "CRITICAL" else "delayed"
        )
        destination_risk = (
            "critical"
            if severity == "CRITICAL"
            else "high"
            if severity == "HIGH"
            else "watch"
            if severity == "MEDIUM"
            else "stable"
        )
        if RISK_WEIGHT[destination_risk] > RISK_WEIGHT[node_risk[destination.location_id]]:
            node_risk[destination.location_id] = destination_risk
        if shipment.status == "DELAYED" and node_risk[source.location_id] == "stable":
            node_risk[source.location_id] = "watch"
        routes.append(
            {
                "route_id": shipment.shipment_id,
                "route_type": "INBOUND_SHIPMENT",
                "source_id": source.location_id,
                "destination_id": destination.location_id,
                "material_id": shipment.material_id,
                "status": route_status,
                "delay_hours": item["delay_hours"] if item else 0,
                "exposure_idr": item["baseline_exposure_idr"] if item else 0,
                "label": f"{source.name} to {destination.name}",
            }
        )

    for option in repo.options:
        source = locations.get(option.source_id)
        destination = locations.get(option.destination_facility_id)
        if source is None or destination is None:
            continue
        routes.append(
            {
                "route_id": f"ALT-{option.option_id}",
                "route_type": "MITIGATION_OPTION",
                "source_id": source.location_id,
                "destination_id": destination.location_id,
                "material_id": option.material_id,
                "status": "available" if option.available else "unavailable",
                "delay_hours": option.arrival_hours,
                "exposure_idr": option.fixed_cost_idr + option.available_quantity * option.variable_cost_per_unit_idr,
                "label": f"{source.name} to {destination.name}",
            }
        )

    nodes = []
    for location in locations.values():
        payload = location.model_dump(mode="json")
        payload["status"] = node_risk[location.location_id]
        nodes.append(payload)

    return {
        "generated_at": repo.demo_now,
        "summary": {
            "facilities": sum(1 for item in nodes if item["location_type"] == "FACTORY"),
            "warehouses": sum(1 for item in nodes if item["location_type"] == "WAREHOUSE"),
            "ports": sum(1 for item in nodes if item["location_type"] == "PORT"),
            "active_routes": sum(1 for item in routes if item["route_type"] == "INBOUND_SHIPMENT"),
            "disrupted_routes": sum(1 for item in routes if item["status"] in {"critical", "delayed"}),
        },
        "nodes": nodes,
        "routes": routes,
    }
