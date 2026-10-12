"""Send one EventBridge-compatible synthetic incident to the local NSRA API."""

from __future__ import annotations

import argparse
import json
import sys

import requests

from integrations.aws_events import eventbridge_to_incident


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    event = {
        "version": "0",
        "id": "INC-LOCAL-EVENT-001",
        "detail-type": "VESSEL_DELAY",
        "source": "local.nsra.event-simulator",
        "time": "2026-10-10T09:00:00+08:00",
        "detail": {
            "severity": "HIGH",
            "title": "Synthetic EventBridge-compatible vessel delay",
            "description": "Local emulation only; no AWS API was called.",
            "shipment_id": "SHP-MKS-001",
            "delay_hours": 12,
        },
    }
    incident = eventbridge_to_incident(event)
    try:
        response = requests.post(
            f"{args.base_url.rstrip('/')}/api/v1/incidents",
            json=incident.model_dump(mode="json"),
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        print("Event simulation failed; verify that the backend is running.", file=sys.stderr)
        return 1
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("AWS status: LOCAL EMULATED; LIVE NOT VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
