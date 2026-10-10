"""AWS EventBridge/Lambda integration boundary for a later phase."""

from __future__ import annotations

from typing import Any


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow normalized event without calling AWS."""

    return {"source": event.get("source", "unknown"), "detail": event.get("detail", {})}

