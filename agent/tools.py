"""Allowlisted NSRA runtime tools for bounded agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from backend.repository import InMemoryRepository
from backend.service import create_transaction_draft, run_deterministic_analysis
from backend.schemas import TransactionDraftCreateRequest


class UnknownToolError(LookupError):
    """Raised when a model or caller requests a non-allowlisted tool."""


class ToolPermissionError(PermissionError):
    """Raised when an agent attempts a side-effecting tool without permission."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]
    side_effecting: bool = False


class ToolRegistry:
    """Explicit tool registry that rejects arbitrary names and side effects."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self.trace: list[str] = []

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name}")
        self._tools[definition.name] = definition

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

    def call(
        self,
        name: str,
        *,
        allow_side_effects: bool = False,
        **kwargs: Any,
    ) -> Any:
        definition = self._tools.get(name)
        if definition is None:
            raise UnknownToolError(f"tool is not allowlisted: {name}")
        if definition.side_effecting and not allow_side_effects:
            raise ToolPermissionError(f"tool requires explicit side-effect permission: {name}")
        self.trace.append(f"{name}: {definition.description}")
        return definition.handler(**kwargs)


def build_tool_registry(repo: InMemoryRepository) -> ToolRegistry:
    """Create the complete runtime registry for one repository instance."""

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="lookup_incident",
            description="Retrieve one normalized incident by ID.",
            handler=lambda incident_id: repo.get_incident(incident_id),
        )
    )
    registry.register(
        ToolDefinition(
            name="get_inventory",
            description="Retrieve inventory for one material and facility.",
            handler=lambda material_id, facility_id: repo.get_inventory(
                material_id, facility_id
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="get_shipments",
            description="Retrieve the shipment linked to an incident.",
            handler=lambda shipment_id: repo.get_shipment(shipment_id),
        )
    )
    registry.register(
        ToolDefinition(
            name="calculate_stockout",
            description="Run deterministic stockout analysis for an incident.",
            handler=lambda incident_id, target_downtime_hours=0: run_deterministic_analysis(
                repo,
                incident_id=incident_id,
                target_downtime_hours=target_downtime_hours,
                persist=False,
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="compare_mitigations",
            description="Return deterministic ranked mitigations for an incident.",
            handler=lambda incident_id, target_downtime_hours=0: run_deterministic_analysis(
                repo,
                incident_id=incident_id,
                target_downtime_hours=target_downtime_hours,
                persist=False,
            ),
        )
    )
    registry.register(
        ToolDefinition(
            name="create_transaction_draft",
            description="Create a simulated reviewable draft; never executes a real order.",
            handler=lambda **payload: create_transaction_draft(
                repo, TransactionDraftCreateRequest.model_validate(payload)
            ),
            side_effecting=True,
        )
    )
    return registry
