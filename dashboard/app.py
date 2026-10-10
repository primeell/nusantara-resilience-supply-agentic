"""Streamlit dashboard shell for local NSRA exploration."""

import streamlit as st

from backend.mock_erp import list_inventory
from backend.inventory import stockout_risk


st.set_page_config(page_title="NSRA", page_icon="🚢", layout="wide")
st.title("Nusantara Supply Resiliency Agent")
st.caption("Local MVP dashboard — mock ERP data only")

rows = [
    {
        "material_id": item.material_id,
        "facility_id": item.facility_id,
        "on_hand": item.on_hand,
        "days_of_cover": round(item.days_of_cover, 1),
        "risk": stockout_risk(item),
    }
    for item in list_inventory()
]
st.dataframe(rows, use_container_width=True, hide_index=True)

