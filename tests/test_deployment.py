"""Static safety checks for the SAP BTP Cloud Foundry deployment bundle."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_uses_port_health_check_and_python_buildpack() -> None:
    manifest = (ROOT / "manifest.yml").read_text(encoding="utf-8")

    assert "python_buildpack" in manifest
    assert "--port $PORT" in manifest
    assert "health-check-http-endpoint: /health" in manifest
    assert "NSRA_STATE_BACKEND: postgresql" in manifest
    assert "NSRA_STATE_PERSISTENCE: durable-cloud" in manifest
    assert "NSRA_POSTGRES_SSLMODE: require" in manifest
    assert "NSRA_STATE_DB_PATH" not in manifest
    assert 'NSRA_LIVE_AI_REQUESTS_ENABLED: "false"' in manifest


def test_manifest_contains_no_secret_values() -> None:
    manifest = (ROOT / "manifest.yml").read_text(encoding="utf-8").lower()

    assert "client_secret" not in manifest
    assert "clientsecret" not in manifest
    assert "access_token" not in manifest
    assert "sap_client_id" not in manifest


def test_cfignore_excludes_local_credentials_and_state() -> None:
    ignored = (ROOT / ".cfignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in ignored
    assert ".venv/" in ignored
    assert ".nsra-local/" in ignored
    assert "*.sqlite3" in ignored


def test_procfile_and_runtime_are_cloud_foundry_compatible() -> None:
    procfile = (ROOT / "Procfile").read_text(encoding="utf-8")
    runtime = (ROOT / "runtime.txt").read_text(encoding="utf-8").strip()

    assert procfile.startswith("web: ")
    assert "--port $PORT" in procfile
    assert runtime == "python-3.13.x"


def test_cloud_runtime_helper_never_contains_secret_values() -> None:
    helper = (ROOT / "scripts" / "configure_cf_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "dotenv_values" in helper
    assert "SAP_CLIENT_SECRET" in helper
    assert "Configured {key}" in helper
    assert "print(value)" not in helper
    assert "write_text" not in helper


def test_cloud_deployment_runbook_uses_hackathon_identity_provider() -> None:
    runbook = (ROOT / "docs" / "CLOUD_DEPLOYMENT.md").read_text(encoding="utf-8")

    assert "--sso `\n  --origin" not in runbook
    assert "auisywroy-platform" in runbook
    assert "hackathon-a-cruel-angel-s-thesis" in runbook


def test_destination_helper_has_no_embedded_credential_values() -> None:
    helper = (ROOT / "scripts" / "configure_destination.py").read_text(
        encoding="utf-8"
    )

    assert "NSRA_SUPPLY_AGENT_A2A" in helper
    assert "clientsecret" in helper
    assert "print(client_secret)" not in helper
    assert "https://nsra-a-cruel-angels-thesis.cfapps.ap10.hana.ondemand.com" in helper
