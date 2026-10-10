"""Placeholder scenario optimization interfaces for the MVP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogisticsScenario:
    """Candidate logistics strategy with an estimated cost and delay."""

    name: str
    cost_usd: float
    delay_days: int


def choose_fastest(scenarios: list[LogisticsScenario]) -> LogisticsScenario | None:
    """Choose the lowest-delay scenario, using cost as a deterministic tie-breaker."""

    return min(scenarios, key=lambda item: (item.delay_days, item.cost_usd), default=None)

