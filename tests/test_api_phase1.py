import httpx
import pytest

pytestmark = pytest.mark.anyio



async def test_inventory_endpoint_returns_mock_items(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/inventory")
    assert response.status_code == 200

    payload = response.json()
    assert payload["mode"] == "mock"
    assert payload["verification"] == "LOCAL MOCK VERIFIED"
    assert len(payload["items"]) >= 5
    assert payload["items"][0]["material_id"] == "MAT-CHEM-A"
    assert payload["items"][0]["usable_quantity"] == 1800



async def test_shipments_endpoint_returns_mock_shipments(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/shipments")
    assert response.status_code == 200

    payload = response.json()
    assert payload["mode"] == "mock"
    assert payload["shipments"][0]["shipment_id"] == "SHP-MKS-001"
    assert payload["shipments"][0]["current_eta"].endswith("+08:00")



async def test_disruption_analysis_happy_path(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/api/v1/analysis/disruption",
        json={
            "material_id": "MAT-001",
            "facility_id": "ID-JKT-01",
            "delay_days": 4,
        },
    )
    assert response.status_code == 200

    payload = response.json()
    analysis = payload["analysis"]
    assert payload["mode"] == "mock"
    assert analysis["delayed_arrival_day"] == 12
    assert analysis["projected_stockout_day"] == 8
    assert analysis["unmet_demand_units"] == 240
    assert analysis["downtime_days"] == 4



async def test_disruption_analysis_rejects_invalid_input(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/analysis/disruption",
        json={
            "material_id": "MAT-001",
            "facility_id": "ID-JKT-01",
            "delay_days": -1,
        },
    )
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert response.json()["trace_id"]



async def test_disruption_analysis_returns_404_for_unknown_item(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/api/v1/analysis/disruption",
        json={
            "material_id": "MAT-999",
            "facility_id": "ID-JKT-01",
            "delay_days": 2,
        },
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "NOT_FOUND"
