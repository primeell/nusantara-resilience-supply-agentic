"""Safely test SAP connectivity, or run an offline mock check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.sap_ai_client import SAPAIClient, SAPConfig, SAPClientError, SAPConfigurationError  # noqa: E402


def main() -> int:
    """Run only mock mode unless the user explicitly passes --live."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make a live SAP API call")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")

    if not args.live:
        print("SAP connection check: MOCK SUCCESS (no network call made)")
        return 0

    try:
        config = SAPConfig.from_env()
        response = SAPAIClient(config).chat(
            "In one sentence, state the main purpose of supply-chain resilience analysis."
        )
        print("SAP connection check: SUCCESS")
        print(f"Model response: {response}")
        return 0
    except (SAPConfigurationError, SAPClientError) as exc:
        print(f"SAP connection check: FAILURE ({exc})")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

