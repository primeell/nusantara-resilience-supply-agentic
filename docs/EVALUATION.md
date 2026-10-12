# NSRA evaluation evidence

Evaluation date: 2026-10-10. Dataset: data/demo_seed.json. All test data is
synthetic and all transaction actions are local simulations.

## Observed automated results

Command:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
~~~

Observed result: **44 passed**. No failed or skipped tests were reported.

Coverage includes:

- exact usable inventory, safety breach, stockout boundary, split arrivals,
  already-stockout, wrong units, and legacy projection;
- scenario feasibility, source conservation, unavailable supplier, normal
  operation, cost/downtime ranking, and no-feasible damage limitation;
- API validation/error envelope, missing IDs, incident idempotency, prompt-text
  sanitization, reset reliability, draft state transition, and audit;
- tool allowlist/permission, grounded live-shaped response, timeout/malformed/
  hallucinated-response fallback;
- EventBridge-compatible normalization, local Lambda idempotency, simulated SAP
  payload, and dashboard HTTP client behavior;
- a mocked end-to-end incident → analysis → recommendation → draft → approval →
  audit workflow.

## Observed HTTP smoke result

With Uvicorn running locally:

~~~powershell
python scripts/demo_smoke.py
~~~

Observed output:

~~~text
SMOKE PASS | coverage=36h | baseline_downtime=60h |
recommendation=SCN-TRANSFER-MKS+LOCAL-MKS | draft=APPROVED
Demo state reset after smoke run.
~~~

Backend health returned status ok. Streamlit health returned ok. The PowerShell
parser reported no syntax error in start_demo.ps1 and stop_demo.ps1.

## Observed dashboard result

The dashboard was rendered in a narrow in-app browser viewport and the complete
flow was exercised:

1. mode and synthetic-data notice rendered;
2. analysis displayed Makassar Factory, Chemical Compound A, 1,800 kg usable,
   36.0h coverage, and baseline stockout timeline;
3. scenario table ranked the mixed transfer + local supplier first;
4. summary displayed 60.0h baseline vs 0.0h recommended modeled downtime and
   Rp45,000,000 action cost;
5. a COMBINED draft reached PENDING_APPROVAL;
6. approval changed it to APPROVED and displayed “no SAP transaction was
   executed”;
7. audit records rendered.

Visual QA also found and fixed a narrow-viewport secondary-button contrast bug.
Heading hierarchy is h1 then h2, controls have visible labels/focus styles,
buttons have a 44px minimum height, and reduced-motion CSS is present.

## Main fixture arithmetic

- Starting usable stock: 2,000 − 200 − 0 = **1,800 kg**.
- Demand: **50 kg/hour**, therefore coverage = 1,800 / 50 = **36 hours**.
- Delayed inbound: hour 96. Baseline shortage is hours 36–95 =
  **60 downtime-equivalent hours**, unmet demand **3,000 kg**.
- Surabaya transfer: 1,800 kg at hour 48. It cannot prevent the first stockout
  and alone leaves **24 hours** downtime.
- Local supplier: 1,200 kg at hour 12; alone it is insufficient.
- Mixed option: 1,200 kg at hour 12 + 1,800 kg at hour 48 bridges demand to hour
  96. Modeled action cost = Rp26,000,000 + Rp19,000,000 = **Rp45,000,000**.
- Air freight: feasible at hour 12, modeled action cost **Rp220,000,000**.
- Objective selects feasible minimum downtime, then minimum total modeled cost;
  therefore the mixed option ranks above air freight for this fixture.

These figures are reproducible assumptions, not production forecasts or claimed
savings.

## Honest limitations

- SAP AI Core live inference was not called during this evaluation. The client
  is implemented and fallback behavior is tested, but live mode remains
  unverified here.
- AWS EventBridge/Lambda is locally emulated; no AWS resource was provisioned.
- SAP Joule is not deployed.
- The repository is in-memory and single-process; restart/reset clears mutable
  analysis, draft, and audit state.
- There is no production authentication/authorization, database, concurrency
  control across processes, real ERP data, or real transaction execution.
- Logistics/cost/reliability parameters are synthetic and require calibration
  from approved historical data before any operational use.
