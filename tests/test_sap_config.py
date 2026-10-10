import pytest

from agent.sap_ai_client import SAPConfig, SAPConfigurationError


def test_sap_config_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("SAP_CLIENT_ID", "SAP_CLIENT_SECRET", "SAP_AUTH_URL", "SAP_AI_API_URL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SAPConfigurationError):
        SAPConfig.from_env()


def test_sap_config_reads_non_secret_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAP_CLIENT_ID", "local-client")
    monkeypatch.setenv("SAP_CLIENT_SECRET", "local-secret")
    monkeypatch.setenv("SAP_AUTH_URL", "https://auth.example.test")
    monkeypatch.setenv("SAP_AI_API_URL", "https://ai.example.test")

    config = SAPConfig.from_env()
    assert config.resource_group == "default"
    assert config.gpt_deployment_id == "d1a82575de60e02a"

