"""Safely transfer approved local SAP runtime settings to a Cloud Foundry app.

The script never prints credential values. It is intentionally separate from
``manifest.yml`` so secrets cannot be committed with the deployment bundle.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = "nsra-a-cruel-angels-thesis"
REQUIRED_KEYS = (
    "SAP_CLIENT_ID",
    "SAP_CLIENT_SECRET",
    "SAP_AUTH_URL",
    "SAP_AI_API_URL",
    "SAP_RESOURCE_GROUP",
    "SAP_GPT_DEPLOYMENT_ID",
)
DEFAULT_SAP_AI_API_VERSION = "2024-12-01-preview"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set NSRA SAP runtime variables without displaying their values."
    )
    parser.add_argument("--app", default=DEFAULT_APP, help="Cloud Foundry app name")
    parser.add_argument(
        "--cf",
        dest="cf_path",
        help="Optional explicit path to cf.exe when it is not yet on PATH",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start (or restage) the app after all variables are accepted",
    )
    return parser


def _run(cf_path: str, arguments: list[str], secrets: list[str]) -> None:
    completed = subprocess.run(
        [cf_path, *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode == 0:
        return
    message = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    for secret in secrets:
        if secret:
            message = message.replace(secret, "[REDACTED]")
    raise RuntimeError(message.strip() or f"cf {' '.join(arguments[:2])} failed")


def main() -> int:
    args = _parser().parse_args()
    cf_path = args.cf_path or shutil.which("cf")
    if not cf_path:
        raise SystemExit("cf CLI was not found. Pass its path with --cf.")

    values = dotenv_values(PROJECT_ROOT / ".env")
    missing = [key for key in REQUIRED_KEYS if not values.get(key)]
    if missing:
        raise SystemExit("Missing required local settings: " + ", ".join(missing))

    selected = {key: str(values[key]) for key in REQUIRED_KEYS}
    selected["SAP_AI_API_VERSION"] = str(
        values.get("SAP_AI_API_VERSION") or DEFAULT_SAP_AI_API_VERSION
    )
    selected["SAP_AI_LIVE_VERIFIED"] = "true"
    secrets = list(selected.values())

    _run(cf_path, ["app", args.app], secrets)
    for key, value in selected.items():
        _run(cf_path, ["set-env", args.app, key, value], secrets)
        print(f"Configured {key}")

    if args.start:
        _run(cf_path, ["restage", args.app], secrets)
        print(f"Restaged {args.app}")
    else:
        print("Runtime configuration complete. Start or restage the app when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
