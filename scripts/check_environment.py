"""Print safe local environment diagnostics for the NSRA workspace."""

from __future__ import annotations

import importlib.util
import platform
import sys


def main() -> int:
    """Print versions and package availability without printing secrets."""

    print(f"platform={platform.platform()}")
    print(f"python={sys.version.split()[0]}")
    for package in ("fastapi", "httpx", "pytest", "streamlit", "dotenv"):
        print(f"{package}_installed={importlib.util.find_spec(package) is not None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

