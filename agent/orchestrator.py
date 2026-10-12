"""Minimal orchestration boundary for future NSRA agent workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from pydantic import ValidationError

from agent.sap_ai_client import SAPClientError, chat_with_sap
from agent.tools import build_tool_registry
from backend.repository import InMemoryRepository
from backend.schemas import AgentDecision, AnalysisResult, OperationMode


@dataclass(frozen=True)
class DisruptionRequest:
    """Input for a future disruption-analysis workflow."""

    message: str


def analyze_disruption(request: DisruptionRequest) -> str:
    """Delegate a bounded analysis request to the configured SAP model."""

    return chat_with_sap(request.message)


def run_bounded_orchestration(
    repo: InMemoryRepository,
    *,
    incident_id: str,
    target_downtime_hours: float = 0,
    use_live_ai: bool = False,
    llm_callable: Callable[[str], str] | None = None,
) -> AnalysisResult:
    """Run a bounded Python planner and optional grounded SAP explanation.

    Tool order is controlled by code because live model tool-calling capability has
    not been verified for this runtime client. GPT-5.4 may explain the computed
    result, but cannot replace scenario IDs, costs, quantities, or feasibility.
    """

    registry = build_tool_registry(repo)
    incident = registry.call("lookup_incident", incident_id=incident_id)
    shipment = registry.call("get_shipments", shipment_id=incident.shipment_id)
    registry.call(
        "get_inventory",
        material_id=shipment.material_id,
        facility_id=shipment.destination_facility_id,
    )
    analysis = registry.call(
        "compare_mitigations",
        incident_id=incident_id,
        target_downtime_hours=target_downtime_hours,
    )

    deterministic_decision = AgentDecision(
        mode=OperationMode.MOCK,
        recommended_scenario_id=analysis.recommended_scenario_id,
        recommendation_rationale=analysis.recommendation_rationale,
        evidence_ids=analysis.evidence_ids,
        warnings=["Deterministic offline planner; no live model call requested."],
        tool_trace=list(registry.trace),
    )
    if not use_live_ai:
        result = analysis.model_copy(update={"agent": deterministic_decision})
        repo.save_analysis(result)
        return result

    prompt = _build_grounded_prompt(analysis)
    call_model = llm_callable or chat_with_sap
    try:
        candidate = _parse_agent_decision(call_model(prompt), analysis, registry.trace)
        result = analysis.model_copy(
            update={
                "mode": OperationMode.LIVE_AI,
                "agent": candidate,
                "recommendation_rationale": candidate.recommendation_rationale,
                "warnings": [*analysis.warnings, *candidate.warnings],
            }
        )
    except (
        SAPClientError,
        ValidationError,
        ValueError,
        json.JSONDecodeError,
        TimeoutError,
        TypeError,
    ):
        fallback = deterministic_decision.model_copy(
            update={
                "mode": OperationMode.FALLBACK,
                "warnings": [
                    "Live SAP AI explanation was unavailable or invalid; deterministic "
                    "recommendation retained."
                ],
            }
        )
        result = analysis.model_copy(
            update={
                "mode": OperationMode.FALLBACK,
                "agent": fallback,
                "warnings": [*analysis.warnings, *fallback.warnings],
            }
        )
    repo.save_analysis(result)
    return result


def _build_grounded_prompt(analysis: AnalysisResult) -> str:
    allowed = {
        "incident_id": analysis.incident_id,
        "recommended_scenario_id": analysis.recommended_scenario_id,
        "baseline": {
            "scenario_id": analysis.baseline.scenario_id,
            "downtime_hours": analysis.baseline.simulation.downtime_hours,
            "total_cost_idr": analysis.baseline.cost_breakdown.total_idr,
        },
        "scenarios": [
            {
                "scenario_id": item.scenario_id,
                "feasible": item.feasible,
                "downtime_hours": item.simulation.downtime_hours,
                "total_cost_idr": item.cost_breakdown.total_idr,
                "rejected_reasons": item.rejected_reasons,
            }
            for item in analysis.scenarios
        ],
        "evidence_ids": analysis.evidence_ids,
    }
    return (
        "Return JSON only with keys recommended_scenario_id, "
        "recommendation_rationale, evidence_ids, warnings. Preserve the provided "
        "recommended_scenario_id and use only supplied evidence IDs. Explain why the "
        "computed recommendation is defensible and explicitly mention uncertainty. "
        "Do not invent values, tools, endpoints, or actions. Structured facts:\n"
        + json.dumps(allowed, ensure_ascii=False)
    )


def _parse_agent_decision(
    raw: str,
    analysis: AnalysisResult,
    tool_trace: list[str],
) -> AgentDecision:
    value = raw.strip()
    if value.startswith("```"):
        value = value.removeprefix("```json").removeprefix("```")
        value = value.removesuffix("```").strip()
    payload = json.loads(value)
    if payload.get("recommended_scenario_id") != analysis.recommended_scenario_id:
        raise ValueError("model changed the deterministic recommendation")
    allowed_evidence = set(analysis.evidence_ids)
    evidence = payload.get("evidence_ids", [])
    if not isinstance(evidence, list) or not set(evidence) <= allowed_evidence:
        raise ValueError("model referenced unknown evidence")
    return AgentDecision(
        mode=OperationMode.LIVE_AI,
        recommended_scenario_id=analysis.recommended_scenario_id,
        recommendation_rationale=str(payload.get("recommendation_rationale", "")).strip(),
        evidence_ids=evidence,
        warnings=[str(item) for item in payload.get("warnings", [])],
        tool_trace=list(tool_trace),
    )
