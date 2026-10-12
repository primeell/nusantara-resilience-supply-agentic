"""Configure the Cloud Foundry PostgreSQL runtime without printing secrets."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = "nsra-a-cruel-angels-thesis"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set the NSRA PostgreSQL runtime on an existing Cloud Foundry app."
    )
    parser.add_argument("--app", default=DEFAULT_APP, help="Cloud Foundry app name")
    parser.add_argument("--cf", dest="cf_path", help="Explicit path to cf.exe")
    parser.add_argument(
        "--start",
        action="store_true",
        help="Restage the app after every setting has been accepted",
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
    database_url = str(values.get("DATABASE_URL") or "")
    if not database_url:
        raise SystemExit("DATABASE_URL is missing from the local .env file.")

    settings = {
        "DATABASE_URL": database_url,
        "NSRA_STATE_BACKEND": "postgresql",
        "NSRA_STATE_PERSISTENCE": "durable-cloud",
        "NSRA_POSTGRES_SSLMODE": str(
            values.get("NSRA_POSTGRES_SSLMODE") or "require"
        ),
    }
    secrets = [database_url]
    _run(cf_path, ["app", args.app], secrets)
    for key, value in settings.items():
        _run(cf_path, ["set-env", args.app, key, value], secrets)
        print(f"Configured {key}")

    if args.start:
        _run(cf_path, ["restage", args.app], secrets)
        print(f"Restaged {args.app}")
    else:
        print("PostgreSQL runtime configured. Restage the app when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
