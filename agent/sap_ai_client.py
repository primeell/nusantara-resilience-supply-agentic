"""Small, credential-safe client for SAP AI Core Generative AI Hub."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx


class SAPConfigurationError(ValueError):
    """Raised when required SAP configuration is missing or invalid."""


class SAPClientError(RuntimeError):
    """Raised when SAP authentication or inference fails."""


@dataclass(frozen=True)
class SAPConfig:
    """Non-secret SAP AI Core configuration loaded from environment variables."""

    client_id: str
    client_secret: str
    auth_url: str
    ai_api_url: str
    resource_group: str = "default"
    gpt_deployment_id: str = ""
    claude_deployment_id: str = ""
    api_version: str = "2024-12-01-preview"

    @classmethod
    def from_env(cls, *, require_credentials: bool = True) -> "SAPConfig":
        """Load configuration and validate required fields without logging values."""

        values = {
            "client_id": os.getenv("SAP_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("SAP_CLIENT_SECRET", "").strip(),
            "auth_url": os.getenv("SAP_AUTH_URL", "").strip().rstrip("/"),
            "ai_api_url": os.getenv("SAP_AI_API_URL", "").strip().rstrip("/"),
            "resource_group": os.getenv("SAP_RESOURCE_GROUP", "default").strip() or "default",
            "gpt_deployment_id": os.getenv("SAP_GPT_DEPLOYMENT_ID", "").strip(),
            "claude_deployment_id": os.getenv(
                "SAP_CLAUDE_DEPLOYMENT_ID", ""
            ).strip(),
            "api_version": os.getenv(
                "SAP_AI_API_VERSION", "2024-12-01-preview"
            ).strip(),
        }
        required = ("client_id", "client_secret", "auth_url", "ai_api_url")
        missing = [name for name in required if not values[name]] if require_credentials else []
        if missing:
            raise SAPConfigurationError(
                "Missing required SAP configuration: " + ", ".join(missing)
            )
        if not values["gpt_deployment_id"]:
            raise SAPConfigurationError("SAP_GPT_DEPLOYMENT_ID must not be empty")
        return cls(**values)


class SAPAIClient:
    """Token-aware client for the configured GPT-5.4 SAP deployment."""

    def __init__(self, config: SAPConfig, *, timeout: float = 20.0) -> None:
        self.config = config
        self.timeout = timeout
        self._access_token: str | None = None

    def _token_url(self) -> str:
        """Return the OAuth token endpoint, accepting either a base or full URL."""

        if self.config.auth_url.endswith("/oauth/token"):
            return self.config.auth_url
        return f"{self.config.auth_url}/oauth/token"

    def _deployment_url(self) -> str:
        """Build the standard SAP AI Core chat-completions endpoint."""

        endpoint = (
            f"{self.config.ai_api_url}/v2/inference/deployments/"
            f"{self.config.gpt_deployment_id}/chat/completions"
        )
        return f"{endpoint}?{urlencode({'api-version': self.config.api_version})}"

    def _get_access_token(self) -> str:
        """Obtain an OAuth token, exposing only sanitized failure messages."""

        try:
            response = httpx.post(
                self._token_url(),
                data={"grant_type": "client_credentials"},
                auth=(self.config.client_id, self.config.client_secret),
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("access_token")
            if not isinstance(token, str) or not token:
                raise SAPClientError("SAP authentication response did not contain an access token")
            self._access_token = token
            return token
        except httpx.TimeoutException as exc:
            raise SAPClientError("SAP authentication timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise SAPClientError(
                f"SAP authentication failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise SAPClientError("SAP authentication request failed") from exc
        except ValueError as exc:
            raise SAPClientError("SAP authentication returned invalid JSON") from exc

    def chat(self, message: str) -> str:
        """Send one supply-chain analysis message to GPT-5.4."""

        prompt = message.strip()
        if not prompt:
            raise ValueError("message must not be empty")

        for attempt in range(2):
            token = self._access_token or self._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "AI-Resource-Group": self.config.resource_group,
                "Content-Type": "application/json",
            }
            body = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an Indonesian maritime supply-chain analyst. "
                            "Identify disruption impacts, assumptions, and practical mitigations."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            }
            try:
                response = httpx.post(
                    self._deployment_url(), headers=headers, json=body, timeout=self.timeout
                )
                if response.status_code == 401 and attempt == 0:
                    self._access_token = None
                    continue
                response.raise_for_status()
                return _extract_text(response.json())
            except httpx.TimeoutException as exc:
                raise SAPClientError("SAP inference timed out") from exc
            except httpx.HTTPStatusError as exc:
                raise SAPClientError(
                    f"SAP inference failed with HTTP {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise SAPClientError("SAP inference request failed") from exc
            except ValueError as exc:
                raise SAPClientError("SAP inference returned an unexpected response") from exc

        raise SAPClientError("SAP inference authentication expired after retry")


def _extract_text(payload: dict[str, Any]) -> str:
    """Extract common chat-completions response shapes without exposing payloads."""

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(first.get("text"), str):
                return first["text"]
    raise SAPClientError("SAP inference response did not contain assistant text")


def chat_with_sap(message: str) -> str:
    """Load local configuration and call GPT-5.4 through SAP AI Core."""

    return SAPAIClient(SAPConfig.from_env()).chat(message)


def configuration_readiness() -> dict[str, bool]:
    """Return non-sensitive readiness flags for health/status endpoints."""

    fields = {
        "client_id": bool(os.getenv("SAP_CLIENT_ID", "").strip()),
        "client_secret": bool(os.getenv("SAP_CLIENT_SECRET", "").strip()),
        "auth_url": bool(os.getenv("SAP_AUTH_URL", "").strip()),
        "ai_api_url": bool(os.getenv("SAP_AI_API_URL", "").strip()),
        "gpt_deployment_id": bool(
            os.getenv("SAP_GPT_DEPLOYMENT_ID", "").strip()
        ),
    }
    return fields
