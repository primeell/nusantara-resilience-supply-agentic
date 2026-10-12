"""Print safe local environment diagnostics for the NSRA workspace."""

from __future__ import annotations

import importlib.util
import platform
import sys
from pathlib import Path


REQUIRED_PACKAGES = ("fastapi", "httpx", "pytest", "streamlit", "dotenv")
SUPPORTED_MINOR_VERSIONS = {(3, 11), (3, 12), (3, 13)}


def main() -> int:
    """Print versions and package availability without printing secrets."""

    python_version = sys.version_info[:3]
    venv_active = sys.prefix != sys.base_prefix
    env_file_present = Path(".env").exists()

    print(f"platform={platform.platform()}")
    print(f"python={sys.version.split()[0]}")
    print(f"python_supported={python_version[:2] in SUPPORTED_MINOR_VERSIONS}")
    print(f"venv_active={venv_active}")
    print(f"venv_prefix={sys.prefix}")
    print(f"env_file_present={env_file_present}")

    for package in REQUIRED_PACKAGES:
        print(f"{package}_installed={importlib.util.find_spec(package) is not None}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

