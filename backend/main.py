"""FastAPI application for the NSRA local MVP."""

from __future__ import annotations

from fastapi import FastAPI

from agent.sap_ai_client import configuration_readiness

app = FastAPI(title="Nusantara Supply Resiliency Agent", version="0.1.0")


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

