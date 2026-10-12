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
    monkeypatch.setenv("SAP_GPT_DEPLOYMENT_ID", "test-gpt-deployment")

    config = SAPConfig.from_env()
    assert config.resource_group == "default"
    assert config.gpt_deployment_id == "test-gpt-deployment"
    assert config.api_version == "2024-12-01-preview"


def test_sap_deployment_url_includes_documented_api_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAP_CLIENT_ID", "local-client")
    monkeypatch.setenv("SAP_CLIENT_SECRET", "local-secret")
    monkeypatch.setenv("SAP_AUTH_URL", "https://auth.example.test")
    monkeypatch.setenv("SAP_AI_API_URL", "https://ai.example.test")
    monkeypatch.setenv("SAP_GPT_DEPLOYMENT_ID", "test-gpt-deployment")

    from agent.sap_ai_client import SAPAIClient

    url = SAPAIClient(SAPConfig.from_env())._deployment_url()
    assert url.endswith("/chat/completions?api-version=2024-12-01-preview")
