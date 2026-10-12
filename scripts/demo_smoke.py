"""Exercise the complete local HTTP workflow against a running backend."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests


class SmokeFailure(RuntimeError):
    """Raised when a required smoke-test invariant is not satisfied."""


def call(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = requests.request(
        method,
        f"{base_url.rstrip('/')}{path}",
        json=body,
        timeout=10,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise SmokeFailure(f"{path} returned non-JSON content") from exc
    if not response.ok:
        message = payload.get("message", "unknown backend error")
        raise SmokeFailure(f"{path} failed with HTTP {response.status_code}: {message}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def run(base_url: str, *, keep_state: bool) -> None:
    call(base_url, "POST", "/api/v1/demo/reset")
    health = call(base_url, "GET", "/health")
    require(health.get("status") == "ok", "health check was not ok")

    analysis = call(
        base_url,
        "POST",
        "/api/v1/analysis/disruption",
        body={"incident_id": "INC-MKS-FOUR-DAY", "use_live_ai": False},
    )["analysis"]
    require(analysis["hours_of_cover"] == 36, "coverage must be exactly 36 hours")
    require(
        analysis["baseline"]["simulation"]["downtime_hours"] == 60,
        "baseline downtime must be exactly 60 hours",
    )
    require(
        analysis["recommended_scenario_id"] == "SCN-TRANSFER-MKS+LOCAL-MKS",
        "unexpected recommended scenario",
    )

    draft = call(
        base_url,
        "POST",
        "/api/v1/transaction-drafts",
        body={
            "incident_id": analysis["incident_id"],
            "analysis_id": analysis["analysis_id"],
            "scenario_id": analysis["recommended_scenario_id"],
            "requested_by": "smoke.operator",
        },
    )["draft"]
    require(draft["status"] == "PENDING_APPROVAL", "draft was not submitted")

    decided = call(
        base_url,
        "POST",
        f"/api/v1/transaction-drafts/{draft['draft_id']}/decision",
        body={
            "action": "APPROVE",
            "actor": "smoke.manager",
            "justification": "Automated local smoke verification.",
        },
    )["draft"]
    require(decided["status"] == "APPROVED", "draft was not approved")

    audit = call(
        base_url,
        "GET",
        "/api/v1/audit?incident_id=INC-MKS-FOUR-DAY",
    )["records"]
    actions = {item["action"] for item in audit}
    require(
        {"ANALYSIS_COMPLETED", "DRAFT_CREATED", "DRAFT_SUBMITTED", "DRAFT_APPROVED"}
        <= actions,
        "audit trail is incomplete",
    )
    print(
        "SMOKE PASS | coverage=36h | baseline_downtime=60h | "
        "recommendation=SCN-TRANSFER-MKS+LOCAL-MKS | draft=APPROVED"
    )
    if not keep_state:
        call(base_url, "POST", "/api/v1/demo/reset")
        print("Demo state reset after smoke run.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--keep-state", action="store_true")
    args = parser.parse_args()
    try:
        run(args.base_url, keep_state=args.keep_state)
    except (requests.RequestException, SmokeFailure) as exc:
        print(f"SMOKE FAIL | {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
