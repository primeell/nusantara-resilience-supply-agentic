"""Judge-friendly Streamlit workflow backed exclusively by the NSRA API."""

from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from dashboard.api_client import APIError, NSRAApiClient

API_URL = os.getenv("NSRA_API_URL", "http://127.0.0.1:8000")

# Keep the original entry point stable for scripts and bookmarks while the
# command-center implementation lives in a focused, testable UI module.
from dashboard.command_center import render_command_center

render_command_center()
st.stop()

st.set_page_config(page_title="NSRA | Supply Resilience", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --nsra-blue: #1E40AF;
        --nsra-blue-soft: #EFF6FF;
        --nsra-amber: #B45309;
        --nsra-green: #047857;
        --nsra-red: #B91C1C;
        --nsra-ink: #0F172A;
        --nsra-muted: #475569;
        --nsra-border: #CBD5E1;
    }
    .stApp { background: #F8FAFC; color: var(--nsra-ink); }
    html, body, [class*="css"] { font-family: "Fira Sans", "Segoe UI", sans-serif; }
    code, [data-testid="stMetricValue"] { font-family: "Fira Code", Consolas, monospace; }
    h1, h2, h3 { letter-spacing: -0.025em; }
    .nsra-header {
        border-left: 6px solid var(--nsra-blue);
        background: #FFFFFF;
        border-radius: 10px;
        padding: 1.15rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, .08);
    }
    .nsra-header h1 { margin: 0; font-size: 1.85rem; color: var(--nsra-ink); }
    .nsra-header p { margin: .35rem 0 0; color: var(--nsra-muted); }
    .nsra-mode {
        display: inline-block;
        background: var(--nsra-blue-soft);
        color: var(--nsra-blue);
        border: 1px solid #BFDBFE;
        border-radius: 999px;
        padding: .25rem .65rem;
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .04em;
    }
    .nsra-notice {
        background: #FFFBEB;
        border: 1px solid #FCD34D;
        border-radius: 8px;
        color: #78350F;
        padding: .75rem 1rem;
        margin: .5rem 0 1rem;
    }
    .nsra-recommendation {
        background: #ECFDF5;
        border: 1px solid #6EE7B7;
        border-left: 6px solid var(--nsra-green);
        border-radius: 10px;
        padding: 1rem 1.2rem;
    }
    button[data-testid^="stBaseButton"] { min-height: 44px; font-weight: 650; }
    button[data-testid="stBaseButton-secondary"] {
        min-height: 44px;
        background: #FFFFFF !important;
        color: var(--nsra-ink) !important;
        border: 1px solid #94A3B8 !important;
    }
    button[data-testid="stBaseButton-primary"] {
        background: var(--nsra-blue) !important;
        color: #FFFFFF !important;
        border-color: var(--nsra-blue) !important;
    }
    button[data-testid^="stBaseButton"]:disabled {
        background: #E2E8F0 !important;
        color: #64748B !important;
    }
    button[data-testid^="stBaseButton"]:focus-visible,
    input:focus-visible,
    textarea:focus-visible {
        outline: 3px solid #93C5FD !important;
        outline-offset: 2px;
    }
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid var(--nsra-border);
        border-radius: 9px;
        padding: .85rem 1rem;
    }
    [data-testid="stAlert"] p { color: var(--nsra-ink) !important; }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _format_idr(value: float | int | None) -> str:
    if value is None:
        return "—"
    return "Rp{:,.0f}".format(value).replace(",", ".")


def _format_time(value: str | None) -> str:
    if not value:
        return "Tidak terjadi dalam horizon"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M %Z")
    except ValueError:
        return "Waktu tidak valid"


def _scenario_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [analysis["baseline"], *analysis["scenarios"]]
    rows: list[dict[str, Any]] = []
    for item in candidates:
        arrivals = item.get("allocations", [])
        earliest = min(
            (allocation["arrival_at"] for allocation in arrivals),
            default=None,
        )
        rejection = "; ".join(item.get("rejected_reasons", [])) or "—"
        rows.append(
            {
                "Peringkat": item.get("rank") or (0 if item["scenario_id"] == "BASELINE-WAIT" else "—"),
                "Skenario": item["name"],
                "ID": item["scenario_id"],
                "Tiba tercepat": _format_time(earliest),
                "Downtime (jam)": item["simulation"]["downtime_hours"],
                "Biaya tindakan": _format_idr(
                    item["cost_breakdown"]["logistics_and_purchase_idr"]
                ),
                "Total termodelkan": _format_idr(item["cost_breakdown"]["total_idr"]),
                "Feasible": "Ya" if item["feasible"] else "Tidak",
                "Alasan ditolak": rejection,
            }
        )
    return rows


def _clear_workflow() -> None:
    for key in ("analysis", "draft", "decision_message"):
        st.session_state.pop(key, None)


client = NSRAApiClient(API_URL)

st.markdown(
    """
    <section class="nsra-header">
      <h1>Nusantara Supply Resiliency Agent</h1>
      <p>Disruption response command center for inter-island industrial supply.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

try:
    system_status = client.status()
    incidents = client.incidents()["incidents"]
    inventory = client.inventory()["items"]
    shipments = client.shipments()["shipments"]
except APIError as exc:
    st.error(str(exc))
    st.info(
        "Jalankan `uvicorn backend.main:app --port 8000`, lalu muat ulang halaman ini."
    )
    st.stop()

top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown(
        f'<span class="nsra-mode">{escape(system_status["verification"])}</span>',
        unsafe_allow_html=True,
    )
with top_right:
    if st.button("Reset demo", width="stretch", help="Muat ulang fixture sintetis"):
        try:
            client.reset_demo()
            _clear_workflow()
            st.success("Data demo berhasil direset.")
            st.rerun()
        except APIError as exc:
            st.error(str(exc))

st.markdown(
    '<div class="nsra-notice"><strong>Data sintetis.</strong> Semua stok, biaya, '
    "rute, supplier, approval, dan transaksi pada layar ini adalah simulasi lokal. "
    "Tidak ada PO atau transfer SAP nyata yang dijalankan.</div>",
    unsafe_allow_html=True,
)

incident_lookup = {item["incident_id"]: item for item in incidents}
shipment_lookup = {item["shipment_id"]: item for item in shipments}
incident_ids = list(incident_lookup)

st.header("1. Pilih gangguan")
selector_col, mode_col, action_col = st.columns([3, 2, 1.4])
with selector_col:
    selected_id = st.selectbox(
        "Incident",
        incident_ids,
        format_func=lambda value: (
            f'{incident_lookup[value]["severity"]} · '
            f'{incident_lookup[value]["title"]} ({value})'
        ),
    )
with mode_col:
    live_configured = bool(system_status["sap_ai"]["configured"])
    use_live_ai = st.checkbox(
        "Gunakan penjelasan SAP AI Core",
        value=False,
        disabled=not live_configured,
        help=(
            "Opsional. Jika gagal, engine otomatis memakai fallback deterministik."
            if live_configured
            else "Kredensial runtime belum dikonfigurasi; mode offline tetap berfungsi."
        ),
    )
with action_col:
    st.write("")
    st.write("")
    analyze_clicked = st.button(
        "Analisis gangguan",
        type="primary",
        width="stretch",
    )

if st.session_state.get("selected_incident_id") != selected_id:
    _clear_workflow()
    st.session_state.selected_incident_id = selected_id

if analyze_clicked:
    try:
        with st.spinner("Mengambil fakta, mensimulasikan stok, dan membandingkan opsi..."):
            st.session_state.analysis = client.analyze(
                selected_id, use_live_ai=use_live_ai
            )["analysis"]
            st.session_state.pop("draft", None)
            st.session_state.pop("decision_message", None)
    except APIError as exc:
        st.error(str(exc))

analysis = st.session_state.get("analysis")
if analysis is None:
    st.info("Pilih kasus lalu tekan **Analisis gangguan** untuk memulai alur demo.")
    st.stop()

incident = incident_lookup[selected_id]
shipment = shipment_lookup[incident["shipment_id"]]
usable = analysis["input_assumptions"]["starting_usable_quantity"]
unit = analysis["input_assumptions"]["quantity_unit"]

st.header("2. Dampak operasional")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Fasilitas", analysis["facility"]["name"])
kpi2.metric("Material", analysis["affected_material"]["name"])
kpi3.metric("Stok usable", f"{usable:,.0f} {unit}")
kpi4.metric("Coverage", f'{analysis["hours_of_cover"]:,.1f} jam')

timeline_a, timeline_b, timeline_c = st.columns(3)
timeline_a.caption("ETA rencana")
timeline_a.write(_format_time(shipment["baseline_eta"]))
timeline_b.caption("ETA terkini akibat gangguan")
timeline_b.write(_format_time(shipment["current_eta"]))
timeline_c.caption("Stockout baseline")
timeline_c.write(_format_time(analysis["stockout_at"]))

st.header("3. Perbandingan skenario")
st.dataframe(
    _scenario_rows(analysis),
    width="stretch",
    hide_index=True,
    column_config={
        "Feasible": st.column_config.TextColumn(help="Memenuhi target downtime dan semua constraint"),
        "Alasan ditolak": st.column_config.TextColumn(width="large"),
    },
)

baseline = analysis["baseline"]
recommended = next(
    item
    for item in [baseline, *analysis["scenarios"]]
    if item["scenario_id"] == analysis["recommended_scenario_id"]
)
comparison_a, comparison_b, comparison_c = st.columns(3)
comparison_a.metric("Downtime baseline", f'{baseline["simulation"]["downtime_hours"]:,.1f} jam')
comparison_b.metric(
    "Downtime rekomendasi",
    f'{recommended["simulation"]["downtime_hours"]:,.1f} jam',
    delta=(
        f'{recommended["simulation"]["downtime_hours"] - baseline["simulation"]["downtime_hours"]:,.1f} jam'
    ),
    delta_color="inverse",
)
comparison_c.metric(
    "Biaya tindakan rekomendasi",
    _format_idr(recommended["cost_breakdown"]["logistics_and_purchase_idr"]),
)

st.header("4. Rekomendasi agent")
agent = analysis.get("agent") or {}
mode_label = {
    "mock": "Mock/offline deterministic",
    "live_ai": "Live SAP AI Core + deterministic engine",
    "fallback": "Offline fallback after AI failure",
}.get(agent.get("mode", analysis["mode"]), "Unknown mode")
with st.container(border=True):
    st.success(f'Rekomendasi: {analysis["recommended_scenario_id"]}')
    st.write(analysis["recommendation_rationale"])
st.caption(f"Mode: {mode_label}")
with st.expander("Bukti, tool trace, dan asumsi"):
    st.write("Evidence IDs:", ", ".join(analysis["evidence_ids"]))
    st.write("Tool trace:")
    st.code("\n".join(agent.get("tool_trace", [])) or "Deterministic service call")
    st.json(analysis["input_assumptions"])
    for warning in analysis["warnings"]:
        st.warning(warning)

st.header("5. Draft transaksi dan persetujuan manusia")
operator_col, draft_col = st.columns([2, 1])
with operator_col:
    requested_by = st.text_input("Operator", value="demo.operator", max_chars=120)
with draft_col:
    st.write("")
    st.write("")
    create_disabled = analysis["draft_action"]["draft_type"] == "NONE"
    if st.button(
        "Buat draft simulasi",
        disabled=create_disabled,
        width="stretch",
        help="Hanya membuat objek lokal untuk direview; tidak mengirim ke SAP.",
    ):
        try:
            st.session_state.draft = client.create_draft(
                incident_id=analysis["incident_id"],
                analysis_id=analysis["analysis_id"],
                scenario_id=analysis["recommended_scenario_id"],
                requested_by=requested_by,
            )["draft"]
        except APIError as exc:
            st.error(str(exc))

draft = st.session_state.get("draft")
if create_disabled:
    st.info("Skenario wait/baseline tidak memerlukan draft transaksi.")
elif draft:
    st.write(
        {
            "draft_id": draft["draft_id"],
            "type": draft["draft_type"],
            "status": draft["status"],
            "estimated_cost": _format_idr(draft["estimated_cost_idr"]),
            "approval_required": draft["requires_approval"],
            "simulation_only": draft["simulated_only"],
        }
    )
    st.dataframe(draft["allocations"], width="stretch", hide_index=True)
    st.caption(draft["approval_policy"])

    if draft["status"] == "PENDING_APPROVAL":
        actor = st.text_input("Approver", value="demo.manager", max_chars=120)
        reason = st.text_area(
            "Justifikasi",
            value="Reviewed against the deterministic scenario comparison.",
            max_chars=500,
        )
        approve_col, reject_col = st.columns(2)
        decision: str | None = None
        if approve_col.button("Approve simulasi", type="primary", width="stretch"):
            decision = "APPROVE"
        if reject_col.button("Reject simulasi", width="stretch"):
            decision = "REJECT"
        if decision:
            try:
                response = client.decide_draft(
                    draft["draft_id"],
                    action=decision,
                    actor=actor,
                    justification=reason,
                )
                st.session_state.draft = response["draft"]
                st.session_state.decision_message = response["message"]
                st.rerun()
            except APIError as exc:
                st.error(str(exc))

if st.session_state.get("decision_message"):
    st.success(st.session_state.decision_message)

st.header("6. Audit trail")
try:
    audit_rows = client.audit(incident_id=selected_id)["records"]
    if audit_rows:
        st.dataframe(audit_rows, width="stretch", hide_index=True)
    else:
        st.info("Belum ada aktivitas untuk incident ini.")
except APIError as exc:
    st.error(str(exc))

st.caption(f"Backend: {API_URL} · OpenAPI: {API_URL}/docs")
