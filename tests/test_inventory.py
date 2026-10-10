from backend.inventory import InventoryItem, stockout_risk


def test_stockout_risk_is_high_when_cover_is_below_lead_time() -> None:
    item = InventoryItem("MAT-1", "FAC-1", on_hand=100, daily_demand=20, lead_time_days=8)
    assert item.days_of_cover == 5
    assert stockout_risk(item) == "high"


def test_stockout_risk_is_low_with_safety_buffer() -> None:
    item = InventoryItem("MAT-2", "FAC-1", on_hand=1000, daily_demand=20, lead_time_days=8)
    assert stockout_risk(item) == "low"

