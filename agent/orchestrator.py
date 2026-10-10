"""Minimal orchestration boundary for future NSRA agent workflows."""

from __future__ import annotations

from dataclasses import dataclass

from agent.sap_ai_client import chat_with_sap


@dataclass(frozen=True)
class DisruptionRequest:
    """Input for a future disruption-analysis workflow."""

    message: str


def analyze_disruption(request: DisruptionRequest) -> str:
    """Delegate a bounded analysis request to the configured SAP model."""

    return chat_with_sap(request.message)

