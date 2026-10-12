"""Small, judge-safe HTTP client used by the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

import requests


class APIError(RuntimeError):
    """Sanitized backend error suitable for display without a stack trace."""


class NSRAApiClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        timeout: float = 10,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise APIError("The backend did not respond before the request timed out.") from exc
        except requests.RequestException as exc:
            raise APIError(
                "The backend is unreachable. Start the API and try again."
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError("The backend returned an invalid response.") from exc

        if not response.ok:
            code = payload.get("error_code", f"HTTP_{response.status_code}")
            message = payload.get("message", "The backend request failed.")
            trace_id = payload.get("trace_id")
            suffix = f" Reference: {trace_id}" if trace_id else ""
            raise APIError(f"{code}: {message}{suffix}")
        if not isinstance(payload, dict):
            raise APIError("The backend returned an unsupported payload shape.")
        return payload

    def status(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/status")

    def inventory(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/inventory")

    def shipments(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/shipments")

    def incidents(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/incidents")

    def analyze(self, incident_id: str, *, use_live_ai: bool = False) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/analysis/disruption",
            json={"incident_id": incident_id, "use_live_ai": use_live_ai},
        )

    def latest_analysis(self, incident_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v1/analyses/latest",
            params={"incident_id": incident_id},
        )

    def drafts(self, *, incident_id: str | None = None) -> dict[str, Any]:
        params = {"incident_id": incident_id} if incident_id else None
        return self._request("GET", "/api/v1/transaction-drafts", params=params)

    def create_draft(
        self,
        *,
        incident_id: str,
        analysis_id: str,
        scenario_id: str,
        requested_by: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/transaction-drafts",
            json={
                "incident_id": incident_id,
                "analysis_id": analysis_id,
                "scenario_id": scenario_id,
                "requested_by": requested_by,
                "idempotency_key": idempotency_key,
            },
        )

    def decide_draft(
        self,
        draft_id: str,
        *,
        action: str,
        actor: str,
        justification: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/api/v1/transaction-drafts/{draft_id}/decision",
            json={
                "action": action,
                "actor": actor,
                "justification": justification,
                "expected_version": expected_version,
            },
        )

    def audit(self, *, incident_id: str | None = None) -> dict[str, Any]:
        params = {"incident_id": incident_id} if incident_id else None
        return self._request("GET", "/api/v1/audit", params=params)

    def reset_demo(self) -> dict[str, Any]:
        return self._request("POST", "/api/v1/demo/reset")
