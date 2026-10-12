# NSRA demonstration script

## 60-second preparation

1. From PowerShell in the repository root, run `./scripts/start_demo.ps1`.
2. Confirm the application opens at `http://127.0.0.1:8000/overview`.
3. Open **Environment details** and reset the workspace if previous demo state exists.
4. Keep SAP AI optional; the presentation must remain independent from internet access.

## Main flow — 5 minutes

### 0:00–0:40 — Executive exposure

Start on **Executive overview**. Explain that the portfolio combines active
incidents, facilities at risk, baseline downtime exposure, and approval state.
Use the exposure trend and facility-material heatmap to establish that this is a
network control tower, not a single-incident mockup.

### 0:40–1:20 — Inter-island network

Open **Supply network**. Point out ports, factories, warehouses, delayed inbound
routes, and critical routes. Select Makassar Factory and show its connected
inbound and mitigation paths. Toggle **Include response options** to explain how
the map distinguishes current logistics from modeled interventions.

### 1:20–2:05 — Incident to production impact

Open **Incident portfolio**, then select `INC-MKS-FOUR-DAY`. State the reviewed
inputs: 1,800 kg usable inventory, 50 kg/hour demand, 36 hours of cover, and an
84-hour shipment delay. Run **Run risk analysis**.

Use the impact chain and hourly projection to show:

- the safety-stock breach and baseline stockout window;
- 60 hours of baseline downtime and IDR 750 million exposure;
- the recommended response line versus the dashed baseline line.

### 2:05–3:10 — Scenario decision

Show **Cost versus downtime frontier** and the precise scenario table. The
recommended mixed response combines 1,800 kg from Surabaya Warehouse and 1,200
kg from a Makassar supplier, reaches zero modeled downtime, and costs IDR 45
million. Explain that every rejected/constraint-failed option remains visible.

The deterministic objective is: satisfy the downtime target, then minimize
downtime and total modeled impact. These are editable reference assumptions, not
a promise of production savings.

### 3:10–4:20 — Human approval and audit

Create the **Response package**. Open **Approval inbox**, review the allocations,
enter an approver different from `operations.planner`, add a rationale, confirm
the simulation boundary, and approve or reject.

Open **Audit explorer** and show analysis, package creation/submission, and human
decision records. Emphasize that approval updates local simulated state only;
no PO or stock transfer is posted to SAP.

### 4:20–5:00 — Integration honesty

Open **Integration health**. Explain the distinction between operational local
services, configured-but-not-called SAP AI, locally emulated AWS events, and the
disabled SAP ERP writeback boundary. This is the implementation path toward
production integration without presenting an unverified connector as live.

## Two-minute backup path

If the browser is unavailable:

1. Open `http://127.0.0.1:8000/docs` and run the disruption analysis endpoint for
   `INC-MKS-FOUR-DAY`.
2. Or run `python scripts/demo_smoke.py --keep-state`.
3. Show the pass result: 36 hours of cover, 60 hours baseline downtime, mixed
   recommendation, and an approved local draft.
4. Run `./scripts/run_tests.ps1` to show the offline test suite.

If SAP AI or internet access is unavailable, remain on the deterministic local
path. That fallback is tested product behavior, not a prerecorded response.
