"""First-party operations workspace delivery checks."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.anyio


async def test_product_workspace_is_served_at_root(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Executive overview" in response.text
    assert 'href="/network"' in response.text
    assert 'href="/approvals"' in response.text
    assert "NSRA · Operations Control Tower" in response.text
    assert "Demo controls" not in response.text
    assert "Synthetic demo data" not in response.text


@pytest.mark.parametrize(
    ("path", "content_type", "sentinel"),
    [
        ("/assets/styles.css", "text/css", "--sidebar-width"),
        ("/assets/app.js", "application/javascript", "runAnalysis"),
        ("/.well-known/agent.json", "application/json", "NSRA Supply Resilience Agent"),
        ("/assets/indonesia-50m.json", "application/json", "Natural Earth"),
    ],
)
async def test_frontend_assets_are_served(
    api_client: httpx.AsyncClient,
    path: str,
    content_type: str,
    sentinel: str,
) -> None:
    response = await api_client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    assert sentinel in response.text


@pytest.mark.parametrize(
    "path",
    [
        "/overview",
        "/network",
        "/incidents",
        "/incidents/INC-MKS-FOUR-DAY",
        "/approvals",
        "/audit",
        "/integrations",
    ],
)
async def test_product_deep_links_serve_the_application_shell(
    api_client: httpx.AsyncClient,
    path: str,
) -> None:
    response = await api_client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="page-root"' in response.text
