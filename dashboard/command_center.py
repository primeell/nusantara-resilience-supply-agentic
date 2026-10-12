"""Professional NSRA operations command center UI."""

from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Any
from uuid import uuid4

import streamlit as st

from dashboard.api_client import APIError, NSRAApiClient

API_URL = os.getenv("NSRA_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="NSRA | Supply Resilience Command Center",
    layout="wide",
    initial_sidebar_state="collapsed",
)

STYLES = """
    <style>
    :root {
        --primary: #0F172A; --secondary: #334155; --accent: #0369A1;
        --accent-soft: #E0F2FE; --success: #047857; --success-soft: #ECFDF5;
        --warning: #B45309; --warning-soft: #FFFBEB; --danger: #B91C1C;
        --danger-soft: #FEF2F2; --ink: #020617; --muted: #475569;
        --border: #E2E8F0; --surface: #FFFFFF; --background: #F8FAFC;
    }
    .stApp { background: var(--background); color: var(--ink); }
    .block-container { max-width: 1480px; padding-top: 1.35rem; padding-bottom: 3rem; }
    html, body, [class*="css"] { font-family: "Segoe UI", "Work Sans", sans-serif; }
    code, [data-testid="stMetricValue"] { font-family: "Cascadia Code", Consolas, monospace; }
    h1, h2, h3 { color: var(--primary); letter-spacing: -.025em; }
    h2 { margin-top: 1.4rem; }
    .nsra-header {
        background: linear-gradient(120deg, #0F172A 0%, #172554 58%, #075985 100%);
        border: 1px solid rgba(255,255,255,.12); border-radius: 16px; color: #FFF;
        padding: 1.4rem 1.55rem; margin-bottom: 1rem;
        box-shadow: 0 12px 30px rgba(15,23,42,.14);
    }
    .nsra-eyebrow { color: #BAE6FD; font-size: .74rem; font-weight: 800; letter-spacing: .14em; }
    .nsra-header h1 { color: #FFF; font-size: clamp(1.65rem, 3vw, 2.25rem); margin: .25rem 0; }
    .nsra-header p { color: #E2E8F0; margin: 0; max-width: 800px; line-height: 1.55; }
    .nsra-badge {
        display: inline-flex; align-items: center; border: 1px solid #CBD5E1;
        border-radius: 999px; background: #FFF; color: var(--secondary);
        font-size: .72rem; font-weight: 800; letter-spacing: .045em;
        padding: .3rem .62rem; text-transform: uppercase; white-space: nowrap;
    }
    .nsra-badge.success { background: var(--success-soft); border-color: #6EE7B7; color: #065F46; }
    .nsra-badge.warning { background: var(--warning-soft); border-color: #FCD34D; color: #78350F; }
    .nsra-badge.danger { background: var(--danger-soft); border-color: #FCA5A5; color: #991B1B; }
    .nsra-badge.info { background: var(--accent-soft); border-color: #7DD3FC; color: #075985; }
    .nsra-notice {
        background: var(--warning-soft); border: 1px solid #FCD34D;
        border-left: 5px solid var(--warning); border-radius: 10px; color: #78350F;
        padding: .8rem 1rem; margin: .65rem 0 1.1rem; line-height: 1.5;
    }
    .nsra-progress { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: .6rem; margin: 1rem 0 1.2rem; }
    .nsra-stage {
        background: #FFF; border: 1px solid var(--border); border-radius: 9px;
        color: var(--muted); padding: .65rem .75rem; font-size: .82rem; font-weight: 700;
    }
    .nsra-stage.active { border-color: #38BDF8; box-shadow: inset 3px 0 0 var(--accent); color: #075985; }
    .nsra-stage.complete { background: var(--success-soft); border-color: #A7F3D0; color: #065F46; }
    .nsra-stage small { display: block; font-size: .67rem; font-weight: 800; letter-spacing: .08em; opacity: .85; }
    .nsra-summarybar {
        position: sticky; top: .5rem; z-index: 20; display: grid;
        grid-template-columns: 1.2fr 1.8fr .8fr; gap: .7rem;
        background: rgba(255,255,255,.97); border: 1px solid #BFDBFE;
        border-left: 5px solid var(--accent); border-radius: 11px;
        box-shadow: 0 8px 22px rgba(15,23,42,.1); padding: .75rem .9rem;
        margin: .8rem 0 1.15rem; backdrop-filter: blur(10px);
    }
    .nsra-summarybar small, .nsra-event small, .nsra-card small { color: var(--muted); display: block; font-weight: 700; }
    .nsra-summarybar strong { color: var(--primary); display: block; margin-top: .12rem; overflow-wrap: anywhere; }
    .nsra-timeline { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: .75rem; margin: .75rem 0 1rem; }
    .nsra-event {
        background: #FFF; border: 1px solid var(--border); border-top: 4px solid #94A3B8;
        border-radius: 10px; min-height: 112px; padding: .8rem .9rem;
    }
    .nsra-event.risk { border-top-color: var(--danger); }
    .nsra-event.response { border-top-color: var(--success); }
    .nsra-event strong { color: var(--primary); display: block; font-size: .93rem; margin: .3rem 0; }
    .nsra-event span { color: var(--muted); font-size: .78rem; }
    .nsra-scenario-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(230px,1fr)); gap: .8rem; margin: .75rem 0 1rem; }
    .nsra-card {
        background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
        padding: 1rem; box-shadow: 0 1px 2px rgba(15,23,42,.05);
    }
    .nsra-card.recommended { border: 2px solid #0EA5E9; box-shadow: 0 8px 22px rgba(14,165,233,.11); }
    .nsra-card.infeasible { background: #FFFDFD; }
    .nsra-card h3 { font-size: 1rem; margin: .65rem 0 .2rem; min-height: 2.4rem; }
    .nsra-card-id { color: var(--muted); font-family: Consolas, monospace; font-size: .7rem; overflow-wrap: anywhere; }
    .nsra-card-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: .65rem; margin-top: .8rem; }
    .nsra-card-metrics div { border-top: 1px solid var(--border); padding-top: .55rem; }
    .nsra-card-metrics strong { display: block; color: var(--primary); font-size: .9rem; }
    .nsra-bar-row { display: grid; grid-template-columns: minmax(150px,1.1fr) 3fr 90px; gap: .65rem; align-items: center; margin: .6rem 0; }
    .nsra-bar-label { color: var(--secondary); font-size: .8rem; font-weight: 700; overflow-wrap: anywhere; }
    .nsra-bar-track { background: #E2E8F0; border-radius: 999px; height: 12px; overflow: hidden; }
    .nsra-bar-fill { background: #64748B; border-radius: 999px; height: 100%; min-width: 3px; }
    .nsra-bar-fill.recommended { background: var(--accent); }
    .nsra-bar-value { color: var(--primary); font-size: .8rem; font-weight: 800; text-align: right; }
    .nsra-recommendation {
        background: var(--success-soft); border: 1px solid #6EE7B7;
        border-left: 6px solid var(--success); border-radius: 12px;
        padding: 1rem 1.15rem; margin: .7rem 0;
    }
    .nsra-recommendation h3 { color: #065F46; margin: 0 0 .35rem; }
    .nsra-recommendation p { color: #064E3B; margin: 0; line-height: 1.55; }
    .nsra-empty { background: #FFF; border: 1px dashed #94A3B8; border-radius: 12px; padding: 1.4rem; text-align: center; color: var(--muted); }
    button[data-testid^="stBaseButton"] { min-height: 44px; font-weight: 700; cursor: pointer; transition: 180ms ease; }
    button[data-testid="stBaseButton-secondary"] { background: #FFF !important; color: var(--primary) !important; border: 1px solid #94A3B8 !important; }
    button[data-testid="stBaseButton-primary"] { background: var(--accent) !important; color: #FFF !important; border-color: var(--accent) !important; }
    button[data-testid^="stBaseButton"]:disabled { background: #E2E8F0 !important; color: #64748B !important; cursor: not-allowed; }
    button[data-testid="stPopoverButton"] {
        min-height: 44px; background: #FFF !important; color: var(--primary) !important;
        border: 1px solid #94A3B8 !important; font-weight: 700; cursor: pointer;
    }
    button[data-testid="stPopoverButton"] p,
    button[data-testid="stPopoverButton"] svg { color: var(--primary) !important; fill: currentColor !important; }
    button[data-testid^="stBaseButton"]:focus-visible, input:focus-visible, textarea:focus-visible, [role="combobox"]:focus-visible {
        outline: 3px solid #38BDF8 !important; outline-offset: 2px;
    }
    [data-testid="stMetric"] { background: #FFF; border: 1px solid var(--border); border-radius: 10px; padding: .82rem .95rem; }
    [data-testid="stMetricLabel"] p { color: var(--muted) !important; }
    [data-testid="stMetricValue"] { color: var(--primary) !important; }
    [data-testid="stMetricDelta"] { color: var(--secondary) !important; }
    [data-testid="stAlert"] { border-radius: 10px; }
    [data-testid="stAlert"] p { color: var(--ink) !important; }
    @media (max-width: 850px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .nsra-progress, .nsra-timeline { grid-template-columns: 1fr 1fr; }
        .nsra-summarybar { position: static; grid-template-columns: 1fr; }
        .nsra-bar-row { grid-template-columns: 1fr; gap: .25rem; }
        .nsra-bar-value { text-align: left; }
    }
    @media (max-width: 520px) {
        .nsra-progress, .nsra-timeline, .nsra-scenario-grid { grid-template-columns: 1fr; }
        .nsra-header { padding: 1.1rem; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }
    }
    </style>
    """


def _format_idr(value: float | int | None) -> str:
    return "—" if value is None else f"IDR {value:,.0f}"


def _format_time(value: str | None) -> str:
    if not value:
        return "Not reached within the horizon"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M %Z")
    except ValueError:
        return "Invalid timestamp"


def _earliest_arrival(item: dict[str, Any]) -> str | None:
    return min(
        (allocation["arrival_at"] for allocation in item.get("allocations", [])),
        default=None,
    )


def _scenario_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in [analysis["baseline"], *analysis["scenarios"]]:
        rank = item.get("rank")
        rows.append(
            {
                "Rank": f"#{rank}" if rank else ("Baseline" if item["scenario_id"] == "BASELINE-WAIT" else "—"),
                "Scenario": item["name"],
                "Scenario ID": item["scenario_id"],
                "Earliest arrival": _format_time(_earliest_arrival(item)),
                "Downtime (hours)": item["simulation"]["downtime_hours"],
                "Action cost": _format_idr(item["cost_breakdown"]["logistics_and_purchase_idr"]),
                "Modeled total": _format_idr(item["cost_breakdown"]["total_idr"]),
                "Feasibility": "Feasible" if item["feasible"] else "Not feasible",
                "Constraints / rejection": "; ".join(item.get("rejected_reasons", [])) or "All modeled constraints passed",
            }
        )
    return rows


def _clear_workflow() -> None:
    for key in ("analysis", "draft", "decision_message", "draft_idempotency_key"):
        st.session_state.pop(key, None)


def _render_progress(analysis: dict[str, Any] | None, draft: dict[str, Any] | None) -> None:
    current = 1
    if analysis:
        current = 2
    if draft:
        current = 3
    if draft and draft["status"] in {"APPROVED", "REJECTED"}:
        current = 4
    labels = ["Select incident", "Review analysis", "Create draft", "Record decision"]
    parts: list[str] = []
    for index, label in enumerate(labels, start=1):
        state = "complete" if index < current else "active" if index == current else ""
        state_label = "Complete" if index < current else "Current" if index == current else "Upcoming"
        parts.append(
            f'<div class="nsra-stage {state}"><small>STEP {index} · {state_label}</small>{escape(label)}</div>'
        )
    st.markdown(f'<div class="nsra-progress">{"".join(parts)}</div>', unsafe_allow_html=True)


def _render_timeline(
    shipment: dict[str, Any], analysis: dict[str, Any], recommended: dict[str, Any]
) -> None:
    events = [
        ("Planned arrival", shipment["baseline_eta"], "Original shipment commitment", ""),
        ("Projected stockout", analysis["stockout_at"], "Continuity risk begins", "risk"),
        ("Disrupted arrival", shipment["current_eta"], "Latest carrier estimate", "risk"),
        ("Mitigation arrival", _earliest_arrival(recommended), "Earliest recommended response", "response"),
    ]
    cards = "".join(
        f'<div class="nsra-event {css_class}"><small>{escape(label.upper())}</small>'
        f'<strong>{escape(_format_time(value))}</strong><span>{escape(detail)}</span></div>'
        for label, value, detail, css_class in events
    )
    st.markdown(
        f'<div class="nsra-timeline" aria-label="Disruption response timeline">{cards}</div>',
        unsafe_allow_html=True,
    )


def _render_scenario_cards(analysis: dict[str, Any]) -> None:
    candidates = [analysis["baseline"], *analysis["scenarios"]]
    recommended_id = analysis["recommended_scenario_id"]
    candidates.sort(
        key=lambda item: (
            item["scenario_id"] != recommended_id,
            item.get("rank") is None,
            item.get("rank") or 999,
        )
    )
    cards: list[str] = []
    for item in candidates:
        is_recommended = item["scenario_id"] == recommended_id
        feasible = item["feasible"]
        card_class = "recommended" if is_recommended else "" if feasible else "infeasible"
        if is_recommended:
            badge = '<span class="nsra-badge info">Recommended</span>'
        elif feasible:
            badge = '<span class="nsra-badge success">Feasible</span>'
        else:
            badge = '<span class="nsra-badge danger">Not feasible</span>'
        rank = f'Rank {item["rank"]}' if item.get("rank") else "Baseline"
        cards.append(
            f'<article class="nsra-card {card_class}">{badge}'
            f'<h3>{escape(item["name"])}</h3><div class="nsra-card-id">{escape(item["scenario_id"])}</div>'
            f'<div class="nsra-card-metrics">'
            f'<div><small>{escape(rank)}</small><strong>{item["simulation"]["downtime_hours"]:,.1f} h downtime</strong></div>'
            f'<div><small>Action cost</small><strong>{escape(_format_idr(item["cost_breakdown"]["logistics_and_purchase_idr"]))}</strong></div>'
            f'<div><small>Earliest arrival</small><strong>{escape(_format_time(_earliest_arrival(item)))}</strong></div>'
            f'<div><small>Reliability signal</small><strong>{"Within constraints" if feasible else "Review rejection"}</strong></div>'
            f'</div></article>'
        )
    st.markdown(
        f'<div class="nsra-scenario-grid" aria-label="Ranked scenario cards">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def _render_downtime_bars(analysis: dict[str, Any]) -> None:
    candidates = [analysis["baseline"], *analysis["scenarios"]]
    maximum = max((item["simulation"]["downtime_hours"] for item in candidates), default=0) or 1
    rows: list[str] = []
    for item in candidates:
        value = item["simulation"]["downtime_hours"]
        width = max(1.5, value / maximum * 100)
        recommended = item["scenario_id"] == analysis["recommended_scenario_id"]
        css_class = "recommended" if recommended else ""
        suffix = " · recommended" if recommended else ""
        rows.append(
            f'<div class="nsra-bar-row" role="img" aria-label="{escape(item["name"])}: {value:,.1f} hours downtime{suffix}">'
            f'<div class="nsra-bar-label">{escape(item["name"])}</div>'
            f'<div class="nsra-bar-track"><div class="nsra-bar-fill {css_class}" style="width:{width:.1f}%"></div></div>'
            f'<div class="nsra-bar-value">{value:,.1f} hours</div></div>'
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def render_command_center() -> None:
    """Render the complete English-language disruption workflow."""

    st.markdown(STYLES, unsafe_allow_html=True)
    client = NSRAApiClient(API_URL)
    st.markdown(
        """
        <header class="nsra-header">
          <div class="nsra-eyebrow">OPERATIONS COMMAND CENTER</div>
          <h1>Nusantara Supply Resiliency Agent</h1>
          <p>Evidence-grounded disruption response for inter-island industrial supply chains, from operational impact to human-approved action.</p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    try:
        system_status = client.status()
        incidents = client.incidents()["incidents"]
        inventory = client.inventory()["items"]
        shipments = client.shipments()["shipments"]
    except APIError as exc:
        st.error(f"Unable to load command center data. {exc}")
        st.info("Start the API with `uvicorn backend.main:app --port 8000`, then retry the connection.")
        if st.button("Retry connection", type="primary"):
            st.rerun()
        return

    status_col, store_col, data_col, control_col = st.columns([1.5, 1, 1.2, 1])
    with status_col:
        st.markdown(f'<span class="nsra-badge success">{escape(system_status["verification"])}</span>', unsafe_allow_html=True)
    with store_col:
        store = system_status.get("state_store", {})
        store_label = "Persistent SQLite" if store.get("persistent") else "Session memory"
        st.markdown(f'<span class="nsra-badge info">{escape(store_label)}</span>', unsafe_allow_html=True)
    with data_col:
        st.markdown('<span class="nsra-badge warning">Synthetic demo data</span>', unsafe_allow_html=True)
    with control_col:
        with st.popover("Demo controls", width="stretch"):
            st.caption("Reset removes analyses, drafts, and audit activity, then reloads the reviewed seed data.")
            if st.button("Reset demo data", width="stretch"):
                try:
                    client.reset_demo()
                    _clear_workflow()
                    st.success("Demo data was reset successfully.")
                    st.rerun()
                except APIError as exc:
                    st.error(str(exc))

    st.markdown(
        '<div class="nsra-notice" role="note"><strong>Simulation boundary.</strong> '
        "All inventory, costs, routes, suppliers, approvals, and transactions shown here are local simulations. "
        "No purchase order or stock transfer is written to SAP.</div>",
        unsafe_allow_html=True,
    )

    incident_lookup = {item["incident_id"]: item for item in incidents}
    shipment_lookup = {item["shipment_id"]: item for item in shipments}
    _render_progress(st.session_state.get("analysis"), st.session_state.get("draft"))

    st.header("1. Select a disruption")
    filter_col, selector_col, mode_col, action_col = st.columns([1.2, 3, 2, 1.35])
    with filter_col:
        severity_filter = st.selectbox(
            "Severity filter",
            ["ALL", "CRITICAL", "HIGH", "MEDIUM", "INFO"],
            format_func=lambda value: "All severities" if value == "ALL" else value.title(),
        )
    filtered_ids = [
        item["incident_id"]
        for item in incidents
        if severity_filter == "ALL" or item["severity"] == severity_filter
    ]
    with selector_col:
        selected_id = st.selectbox(
            "Incident",
            filtered_ids,
            format_func=lambda value: (
                f'{incident_lookup[value]["severity"]} · '
                f'{incident_lookup[value]["title"]} ({value})'
            ),
        )
    with mode_col:
        live_configured = bool(system_status["sap_ai"]["configured"])
        use_live_ai = st.checkbox(
            "Use SAP AI Core explanation",
            value=False,
            disabled=not live_configured,
            help=(
                "Optional. If the AI call fails, the engine uses a deterministic fallback."
                if live_configured
                else "Runtime credentials are not configured. Offline analysis remains available."
            ),
        )
    with action_col:
        st.write("")
        st.write("")
        analyze_clicked = st.button("Analyze disruption", type="primary", width="stretch")

    if st.session_state.get("selected_incident_id") != selected_id:
        _clear_workflow()
        st.session_state.selected_incident_id = selected_id

    if st.session_state.get("analysis") is None:
        try:
            resumed_analysis = client.latest_analysis(selected_id).get("analysis")
            if resumed_analysis:
                st.session_state.analysis = resumed_analysis
                existing_drafts = client.drafts(incident_id=selected_id)["drafts"]
                matching_drafts = [
                    item
                    for item in existing_drafts
                    if item["analysis_id"] == resumed_analysis["analysis_id"]
                ]
                if matching_drafts:
                    st.session_state.draft = max(
                        matching_drafts, key=lambda item: item["created_at"]
                    )
                else:
                    st.session_state.draft_idempotency_key = uuid4().hex
        except APIError as exc:
            st.warning(f"Saved workflow state could not be restored. {exc}")

    if analyze_clicked:
        try:
            with st.status("Analyzing the disruption...", expanded=True) as status_box:
                st.write("Loading inventory, shipment, and incident evidence.")
                st.write("Simulating time-phased stock and ranking constrained response options.")
                st.session_state.analysis = client.analyze(
                    selected_id, use_live_ai=use_live_ai
                )["analysis"]
                st.session_state.pop("draft", None)
                st.session_state.pop("decision_message", None)
                st.session_state.draft_idempotency_key = uuid4().hex
                status_box.update(label="Analysis complete", state="complete", expanded=False)
        except APIError as exc:
            st.error(f"Analysis failed. {exc}")
            st.info("Verify backend health, then select **Analyze disruption** to retry.")

    analysis = st.session_state.get("analysis")
    if analysis is None:
        st.markdown(
            '<div class="nsra-empty"><strong>No active analysis</strong><br>Select an incident and run the analysis to compare continuity options.</div>',
            unsafe_allow_html=True,
        )
        return

    incident = incident_lookup[selected_id]
    shipment = shipment_lookup[incident["shipment_id"]]
    baseline = analysis["baseline"]
    recommended = next(
        item for item in [baseline, *analysis["scenarios"]]
        if item["scenario_id"] == analysis["recommended_scenario_id"]
    )
    usable = analysis["input_assumptions"]["starting_usable_quantity"]
    unit = analysis["input_assumptions"]["quantity_unit"]
    decision_status = (st.session_state.get("draft") or {}).get("status", "ANALYZED")

    st.markdown(
        '<div class="nsra-summarybar">'
        f'<div><small>ACTIVE INCIDENT</small><strong>{escape(incident["title"])}</strong></div>'
        f'<div><small>RECOMMENDED RESPONSE</small><strong>{escape(recommended["name"])}</strong></div>'
        f'<div><small>WORKFLOW STATUS</small><strong>{escape(decision_status.replace("_", " ").title())}</strong></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.header("2. Operational impact")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Facility", analysis["facility"]["name"])
    kpi2.metric("Affected material", analysis["affected_material"]["name"])
    kpi3.metric("Usable inventory", f"{usable:,.0f} {unit}")
    kpi4.metric("Time to stockout", f'{analysis["hours_of_cover"]:,.1f} hours')
    _render_timeline(shipment, analysis, recommended)

    st.header("3. Ranked response scenarios")
    _render_scenario_cards(analysis)
    chart_col, outcome_col = st.columns([1.5, 1])
    with chart_col:
        st.subheader("Downtime comparison")
        _render_downtime_bars(analysis)
    with outcome_col:
        st.subheader("Recommendation impact")
        downtime_saved = baseline["simulation"]["downtime_hours"] - recommended["simulation"]["downtime_hours"]
        modeled_value = baseline["cost_breakdown"]["total_idr"] - recommended["cost_breakdown"]["total_idr"]
        st.metric("Downtime avoided", f"{downtime_saved:,.1f} hours")
        st.metric("Modeled value protected", _format_idr(modeled_value))
        st.metric("Action cost", _format_idr(recommended["cost_breakdown"]["logistics_and_purchase_idr"]))

    with st.expander("Open full scenario evidence table"):
        st.dataframe(
            _scenario_rows(analysis),
            width="stretch",
            hide_index=True,
            column_config={
                "Feasibility": st.column_config.TextColumn(help="Whether the option satisfies target downtime and modeled constraints."),
                "Constraints / rejection": st.column_config.TextColumn(width="large"),
            },
        )

    st.header("4. Agent recommendation")
    agent = analysis.get("agent") or {}
    mode_label = {
        "mock": "Deterministic offline engine",
        "live_ai": "SAP AI Core explanation with deterministic calculations",
        "fallback": "Deterministic fallback after AI unavailability",
    }.get(agent.get("mode", analysis["mode"]), "Unknown mode")
    st.markdown(
        '<section class="nsra-recommendation">'
        f'<h3>Recommended: {escape(recommended["name"])}</h3>'
        f'<p>{escape(analysis["recommendation_rationale"])}</p></section>',
        unsafe_allow_html=True,
    )
    st.caption(f"Decision mode: {mode_label}")
    with st.expander("Review evidence, tool trace, and assumptions"):
        st.write("Evidence IDs:", ", ".join(analysis["evidence_ids"]))
        st.write("Tool trace:")
        st.code("\n".join(agent.get("tool_trace", [])) or "Deterministic service call")
        st.json(analysis["input_assumptions"])
        for warning in analysis["warnings"]:
            st.warning(warning)

    st.header("5. Human approval")
    draft = st.session_state.get("draft")
    create_disabled = analysis["draft_action"]["draft_type"] == "NONE"
    operator_col, draft_col = st.columns([2, 1])
    with operator_col:
        requested_by = st.text_input(
            "Requesting operator",
            value="demo.operator",
            max_chars=120,
            disabled=bool(draft),
            help="Demo identity only. Production deployment should use SSO-derived identity.",
        )
    with draft_col:
        st.write("")
        st.write("")
        create_clicked = st.button(
            "Create simulated draft" if not draft else "Draft already created",
            disabled=create_disabled or bool(draft) or not requested_by.strip(),
            width="stretch",
            help="Creates a local review object only. Nothing is sent to SAP.",
        )

    if create_clicked:
        try:
            with st.spinner("Creating an idempotent simulation draft..."):
                st.session_state.draft = client.create_draft(
                    incident_id=analysis["incident_id"],
                    analysis_id=analysis["analysis_id"],
                    scenario_id=analysis["recommended_scenario_id"],
                    requested_by=requested_by.strip(),
                    idempotency_key=st.session_state.get("draft_idempotency_key") or uuid4().hex,
                )["draft"]
                st.rerun()
        except APIError as exc:
            st.error(f"Draft creation failed. {exc}")
            st.info("The request is idempotent. Correct the issue and retry without creating a duplicate draft.")

    draft = st.session_state.get("draft")
    if create_disabled:
        st.info("The baseline wait scenario does not require a transaction draft.")
    elif draft:
        draft_a, draft_b, draft_c, draft_d = st.columns(4)
        draft_a.metric("Draft ID", draft["draft_id"])
        draft_b.metric("Status", draft["status"].replace("_", " ").title())
        draft_c.metric("Estimated action cost", _format_idr(draft["estimated_cost_idr"]))
        draft_d.metric("Version", draft.get("version", 1))
        with st.expander("Review proposed allocation details", expanded=True):
            st.dataframe(draft["allocations"], width="stretch", hide_index=True)
            st.caption(draft["approval_policy"])

        if draft["status"] == "PENDING_APPROVAL":
            st.subheader("Record a controlled decision")
            with st.form("approval_form", clear_on_submit=False):
                actor = st.text_input(
                    "Approver identity",
                    value="demo.manager",
                    max_chars=120,
                    help="Must be different from the requesting operator.",
                )
                reason = st.text_area(
                    "Decision rationale",
                    value="Reviewed against the deterministic scenario comparison and modeled constraints.",
                    max_chars=500,
                    help="Provide at least 10 characters so the audit record remains meaningful.",
                )
                acknowledged = st.checkbox(
                    "I understand that this approval changes only the local simulation state and does not execute an SAP transaction."
                )
                approve_col, reject_col = st.columns(2)
                approve = approve_col.form_submit_button(
                    "Approve simulated draft", type="primary", width="stretch"
                )
                reject = reject_col.form_submit_button(
                    "Reject simulated draft", width="stretch"
                )
            if approve or reject:
                if not acknowledged:
                    st.error("Confirm the simulation boundary before recording a decision.")
                elif actor.strip() == draft["requested_by"].strip():
                    st.error("The approver must be different from the requesting operator.")
                elif len(reason.strip()) < 10:
                    st.error("Enter a decision rationale of at least 10 characters.")
                else:
                    try:
                        response = client.decide_draft(
                            draft["draft_id"],
                            action="APPROVE" if approve else "REJECT",
                            actor=actor.strip(),
                            justification=reason.strip(),
                            expected_version=draft.get("version", 1),
                        )
                        st.session_state.draft = response["draft"]
                        st.session_state.decision_message = response["message"]
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Decision submission failed. {exc}")
                        st.info("Refresh the draft state before retrying if another approver changed it.")

    if st.session_state.get("decision_message"):
        st.success(st.session_state.decision_message)

    st.header("6. Audit trail")
    try:
        audit_rows = client.audit(incident_id=selected_id)["records"]
        if audit_rows:
            st.dataframe(audit_rows, width="stretch", hide_index=True)
        else:
            st.info("No activity has been recorded for this incident yet.")
    except APIError as exc:
        st.error(f"Audit trail could not be loaded. {exc}")
        st.info("Verify backend health and reload this section.")

    st.caption(
        f"Backend: {API_URL} · OpenAPI: {API_URL}/docs · "
        f"Inventory records loaded: {len(inventory)} · Transactions: simulation only"
    )
