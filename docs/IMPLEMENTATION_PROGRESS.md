# Implementation progress

**Status date:** 2026-10-13

**Active development branch:** `codex/control-tower-ui-v2`

**Application version:** `0.5.0`

This document records the implemented scope and the evidence level of each subsystem. It distinguishes repository capability from the revision currently running in Cloud Foundry.

## Executive summary

NSRA now supports an end-to-end, human-governed resilience workflow using deterministic synthetic data:

1. ingest or select a disruption;
2. calculate hourly inventory exposure;
3. enumerate and validate mitigation scenarios;
4. recommend the best feasible response under bounded rules;
5. prepare a simulated transaction package;
6. require a separate human approver;
7. preserve the decision in an audit trail; and
8. expose a read-only briefing through SAP Joule.

The solution is ready for a credible product demonstration and technical review. It is not yet production-ready because the public cloud revision still uses ephemeral SQLite, public API authorization is not implemented, AWS resources are not live, operational data is synthetic, and SAP ERP writeback is intentionally absent.

## Delivery matrix

| Capability | Repository | Local evidence | External evidence | Current assessment |
|---|---:|---:|---:|---|
| FastAPI API and structured errors | Complete | 86-test suite passed | Public health endpoint verified | Ready for demo |
| Responsive control-tower interface | Complete | Manually verified | Public deployment is an older revision | Redeploy current branch |
| Executive overview and global filters | Complete | Verified | Not reverified on latest cloud revision | Ready locally |
| Indonesia network map and route inspection | Complete | Verified | Not reverified on latest cloud revision | Ready locally |
| Incident portfolio and workspace | Complete | Verified | Not reverified on latest cloud revision | Ready locally |
| Hourly inventory projection | Complete | Automated and manual verification | None required | Ready |
| Scenario optimizer and frontier | Complete | Automated and manual verification | None required | Ready |
| Approval inbox and audit trail | Complete | Workflow tests and smoke test | External ERP side effects disabled | Safe simulation |
| CSV export, sorting, filtering, pagination | Complete | Frontend tests and manual verification | None required | Ready |
| SQLite local persistence | Complete | Restart/persistence tests | Not a cloud target | Ready for local work |
| PostgreSQL backend and migration | Complete | Configuration and tooling tests | Managed endpoint not provisioned | Infrastructure pending |
| SAP AI Core explanation | Complete | Fallback tested | Controlled live inference recorded | Live verified, restricted |
| SAP Joule A2A briefing | Complete | Contract tests | Tenant invocation previously succeeded | Live verified, read-only |
| AWS EventBridge/Lambda ingestion | Adapter complete | Local emulation verified | No AWS resource call | Live setup pending |
| SAP transaction payload mapping | Complete | Unit verified | No S/4HANA call | Deliberately disabled |
| Authentication and role-based access | Not complete | Not applicable | Not applicable | Production blocker |
| Production monitoring and alerting | Not complete | Basic logs only | Not applicable | Production blocker |

## Implemented product surfaces

### Executive overview

- Active incident, critical-facility, downtime-exposure, and approval KPIs.
- Severity and exposure trends.
- Facility-material risk heatmap.
- Priority-incident portfolio.
- Global filters and “what changed” operational briefing.

### Supply network

- Indonesia geography from a versioned TopoJSON asset.
- Ports, factories, warehouses, suppliers, inbound routes, and mitigation routes.
- Route status, delay, modeled exposure, and selected-node detail.
- Full-screen mode and response-option visibility controls.

### Incident decision workspace

- Resumable subnavigation and URL state.
- Incident-to-production impact chain.
- Full-width hourly inventory projection with 24-hour, 72-hour, and full-horizon views.
- Safety-stock threshold, stockout window, baseline, recommended response, tooltip, and CSV export.
- Cost-versus-downtime scenario frontier with selected-scenario detail.
- Allocation composition and scenario table.

### Governance

- Idempotent incident ingestion and draft creation.
- `DRAFT` to `PENDING_APPROVAL` to `APPROVED` or `REJECTED` state machine.
- Separation of duties between requester and approver.
- Optimistic version check for stale decisions.
- Searchable audit records and correlation IDs.
- Explicit `simulated_only` boundary.

## Deterministic decision behavior

For the primary synthetic incident `INC-MKS-FOUR-DAY`, the expected reference result is:

| Measure | Reference value |
|---|---:|
| Usable inventory | 1,800 kg |
| Demand | 50 kg/hour |
| Hours of cover | 36 hours |
| Shipment delay | 84 hours |
| Baseline downtime | 60 hours |
| Baseline modeled exposure | IDR 750,000,000 |
| Recommended scenario | `SCN-TRANSFER-MKS+LOCAL-MKS` |
| Recommended allocation | 1,800 kg transfer + 1,200 kg local supply |
| Recommended modeled downtime | 0 hours |
| Recommended response cost | IDR 45,000,000 |

These values are test fixtures and reference assumptions, not forecasts or guaranteed savings.

## Current cloud facts

Read-only verification on 2026-10-13 confirmed that the public route responds successfully at:

`https://nsra-a-cruel-angels-thesis.cfapps.ap10.hana.ondemand.com`

The deployed `/api/v1/status` response currently reports:

- application version `0.5.0`;
- production environment;
- SAP AI live verification recorded;
- public live AI requests disabled;
- real transactions disabled; and
- **SQLite with `ephemeral-instance` scope**.

This means the public runtime is healthy but has not yet been moved to the repository's PostgreSQL cloud target. The current branch must be deployed only after a managed TLS-enabled PostgreSQL endpoint has been configured. The Cloud Foundry CLI session also requires interactive reauthentication before management commands can be used again.

## Known limitations

- The synthetic seed is useful for reproducibility but does not represent live inventory, shipment, supplier, weather, or port telemetry.
- The deployment does not yet have durable PostgreSQL state.
- API routes have no end-user authentication or role-based authorization.
- The production-safe policy disables public on-demand SAP AI requests; the deterministic path remains available.
- AWS event ingestion is a local contract adapter, not a deployed EventBridge rule or Lambda function.
- SAP ERP payloads are generated for review but never transmitted.
- The repository uses a process-level write lock; horizontal scaling requires a stronger concurrency strategy.
- There is no browser automation suite yet; frontend behavior is tested structurally and manually.
- There is no centralized telemetry, alert policy, backup test, disaster-recovery exercise, or SLO.

## Next release gate

The next cloud release should not be considered complete until all of the following are true:

1. a managed PostgreSQL endpoint is provisioned with TLS;
2. the current branch is deployed with `NSRA_STATE_BACKEND=postgresql`;
3. `/api/v1/status` reports `engine: postgresql`, `persistent: true`, and `scope: durable-cloud`;
4. state survives an app restage;
5. public mutation routes are protected or disabled;
6. the automated tests, smoke test, secret scan, and dependency audit pass; and
7. the status, integration, and evaluation documents are updated with new evidence.

See [Roadmap](ROADMAP.md) for the complete prioritized plan.
