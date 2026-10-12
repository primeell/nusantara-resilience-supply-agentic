"""Configure the private BTP destination used by the NSRA Joule capability."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from typing import Any

import httpx


DEFAULT_SERVICE_INSTANCE = "nsra-destination"
DEFAULT_SERVICE_KEY = "nsra-destination-config-key"
DESTINATION_NAME = "NSRA_SUPPLY_AGENT_A2A"
DESTINATION_URL = "https://nsra-a-cruel-angels-thesis.cfapps.ap10.hana.ondemand.com/a2a"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update the private NSRA A2A BTP destination."
    )
    parser.add_argument("--cf", help="Optional explicit path to cf.exe")
    parser.add_argument("--service-instance", default=DEFAULT_SERVICE_INSTANCE)
    parser.add_argument("--service-key", default=DEFAULT_SERVICE_KEY)
    return parser


def _service_key(cf_path: str, instance: str, key: str) -> dict[str, Any]:
    completed = subprocess.run(
        [cf_path, "service-key", instance, key],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError("Could not retrieve the configured Destination service key.")
    json_start = completed.stdout.find("{")
    if json_start < 0:
        raise RuntimeError("Destination service key did not contain JSON credentials.")
    payload = json.loads(completed.stdout[json_start:])
    credentials = payload.get("credentials")
    return credentials if isinstance(credentials, dict) else payload


def _scrub(message: str, values: list[str]) -> str:
    for value in values:
        if value:
            message = message.replace(value, "[REDACTED]")
    return message


def main() -> int:
    args = _parser().parse_args()
    cf_path = args.cf or shutil.which("cf")
    if not cf_path:
        raise SystemExit("cf CLI was not found. Pass its path with --cf.")

    credentials = _service_key(cf_path, args.service_instance, args.service_key)
    client_id = str(credentials.get("clientid", ""))
    client_secret = str(credentials.get("clientsecret", ""))
    auth_url = str(credentials.get("url", "")).rstrip("/")
    service_uri = str(credentials.get("uri", "")).rstrip("/")
    if not all((client_id, client_secret, auth_url, service_uri)):
        raise SystemExit("Destination service key is missing required credentials.")

    protected_values = [client_id, client_secret, auth_url, service_uri]
    destination = {
        "Name": DESTINATION_NAME,
        "Type": "HTTP",
        "URL": DESTINATION_URL,
        "ProxyType": "Internet",
        "Authentication": "NoAuthentication",
        "HTML5.DynamicDestination": True,
        "WebIDEEnabled": True,
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            token_response = client.post(
                f"{auth_url}/oauth/token",
                auth=(client_id, client_secret),
                data={"grant_type": "client_credentials"},
            )
            token_response.raise_for_status()
            access_token = str(token_response.json()["access_token"])
            protected_values.append(access_token)
            headers = {"Authorization": f"Bearer {access_token}"}
            collection_url = (
                f"{service_uri}/destination-configuration/v1/subaccountDestinations"
            )
            item_url = f"{collection_url}/{DESTINATION_NAME}"
            exists = client.get(item_url, headers=headers)
            if exists.status_code == 404:
                response = client.post(
                    collection_url,
                    headers={**headers, "Content-Type": "application/json"},
                    json=destination,
                )
            else:
                exists.raise_for_status()
                # Updates target the collection endpoint; Name in the body
                # identifies the destination to replace.
                response = client.put(
                    collection_url,
                    headers={**headers, "Content-Type": "application/json"},
                    json=destination,
                )
            response.raise_for_status()
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise SystemExit(_scrub(str(exc), protected_values)) from exc

    print(f"Configured destination {DESTINATION_NAME}")
    print(f"Target URL: {DESTINATION_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
