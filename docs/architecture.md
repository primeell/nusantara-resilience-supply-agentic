# NSRA architecture

## Implemented local architecture

NSRA uses a maintainable modular monolith. Reviewed reference fixtures remain in
JSON, while mutable incidents, analyses, drafts, counters, and audit records are
persisted as schema-validated snapshots in a local SQLite database. This gives
the local application restart durability without claiming production database readiness.

~~~text
EventBridge-compatible JSON      First-party web application
            |                            |
            v                            v
   AWS contract adapter  --->  FastAPI /api/v1
                                      |
                  +-------------------+-------------------+
                  |                   |                   |
                  v                   v                   v
          SQLite repository     Deterministic engine   Approval/audit
          + JSON fixtures       hourly stock + cost    simulated only
                  |                   |
                  +---------+---------+
                            v
                 Bounded tool orchestrator
                    |                 |
          offline decision      optional SAP AI Core
          always available      grounded explanation
                    |                 |
                    +--------+--------+
                             v
                 schema-validated recommendation
~~~

### Trust boundaries

- Event titles/descriptions are untrusted and sanitized before they can enter an
  AI prompt.
- Numerical truth comes only from Python: stock, ETA, feasibility, allocation,
  cost, ranking, and approval policy.
- The model may explain one deterministic recommendation but cannot replace its
  scenario ID or cite unknown evidence.
- Tool names are allowlisted. Draft creation is side-effecting and denied unless
  a caller explicitly grants that local permission.
- Approval writes only to durable local simulated state. Draft creation is
  idempotent, decisions use optimistic version checks, and the SAP adapter only
  builds a simulation-marked payload without transmitting it.

### Deterministic flow

1. Normalize an incident and resolve shipment, PO, material, and destination.
2. Calculate usable stock and simulate hourly demand with arrivals-before-demand.
3. Enumerate baseline, single-option, and two-option mitigation candidates.
4. Validate material, unit, destination, source capacity, MOQ, availability,
   dispatch cutoff, and lead-time components.
5. Rank feasible candidates lexicographically by downtime then total modeled
   cost. If none is feasible, report the least-damaging candidate honestly.
6. Optionally ask SAP GPT-5.4 for a grounded explanation; validate its JSON and
   fall back to the deterministic explanation on timeout or invalid output.
7. Create an idempotent reviewable draft, require a different human approver,
   enforce a version-checked decision, and append durable audit events.

### Deployment status

- Local application and API: **MOCK VERIFIED**.
- SAP AI Core client and offline fallback: implemented; live inference was not
  invoked in this build session.
- AWS EventBridge/Lambda payload: **LOCAL EMULATED; LIVE NOT VERIFIED**.
- SAP Joule: capability contract/planning only; **NOT DEPLOYED**.
- Real SAP business transaction writes: deliberately **NOT IMPLEMENTED**.

---

## Legacy initial architecture notes

## Components

- **FastAPI backend**: local API boundary for health, readiness, and later domain endpoints.
- **Agent layer**: orchestration boundary plus the SAP AI Core GPT-5.4 client.
- **Inventory and mock ERP**: deterministic local data interfaces for testing without SAP access.
- **Optimization**: small scenario-selection interface, ready to be replaced by a richer optimizer.
- **Web control tower**: responsive incident, scenario, approval, and audit
  workspace served by FastAPI from the same origin.
- **Legacy Streamlit interface**: retained for compatibility but not launched by
  the default application script.
- **SAP adapter**: future SAP business-data integration boundary.
- **AWS events adapter**: future EventBridge/Lambda event normalization boundary.

## Data flow

1. A future event or user request enters the FastAPI boundary.
2. Inventory and disruption data are normalized through backend/integration interfaces.
3. The orchestrator assembles a bounded analysis prompt.
4. SAP AI Core calls the configured GPT-5.4 deployment with an OAuth token obtained from the local service credential.
5. The application returns recommendations for human review; it does not automatically execute operational changes.
6. Approved actions can later flow to SAP and AWS integration adapters.

## SAP AI Core integration

The client reads `SAP_CLIENT_ID`, `SAP_CLIENT_SECRET`, `SAP_AUTH_URL`, and `SAP_AI_API_URL` from the local environment. It requests an OAuth client-credentials token, then calls the configured GPT-5.4 deployment with `AI-Resource-Group: default`. Tokens and credential response bodies are never logged.

## Future AWS integration

EventBridge can deliver disruption events to a Lambda or containerized endpoint. AWS Region and event metadata should remain configuration-driven. No AWS resources are created by this starter workspace.

## Human in the loop

NSRA should present assumptions, confidence, affected facilities/materials, alternatives, and estimated trade-offs to a responsible operator. SAP or logistics actions should require explicit review and approval, with an auditable record of the decision.
