# Evaluation and verification evidence

**Verification date:** 2026-10-15

**Application version:** `0.5.0`

**Branch evaluated:** `codex/control-tower-ui-v2`

This document records reproducible evidence for the current repository. It does not treat configuration, login success, or an implementation stub as proof of a live integration.

## Latest quality-gate result

| Check | Result | Evidence |
|---|---|---|
| Automated test suite | **Pass** | 86 tests executed successfully on Python 3.12.9 |
| Secret scan | **Pass** | 111 tracked/untracked non-ignored repository files scanned |
| Dependency consistency | **Pass** | `pip check`: no broken requirements |
| Dependency vulnerability audit | **Pass** | `pip-audit -r requirements.txt`: no known vulnerabilities |
| End-to-end smoke workflow | **Pass** | Health, analysis, reference recommendation, simulated approval, audit, and reset completed |
| Documentation links | **Pass** | Internal Markdown targets resolved across 20 documentation files |
| Public application health | **Pass** | `/health` returned `status: ok` and `service: nsra-api` |
| Public status disclosure | **Pass with gap identified** | Safe status response; deployment still reports ephemeral SQLite |
| Public A2A discovery | **Pass** | `/.well-known/agent.json` returned the read-only NSRA agent card |
| Cloud Foundry management check | **Authentication required** | Existing CLI token had expired; interactive login is required before management commands |

The repository-local `.venv` contained Python 3.13 binary wheels while its
interpreter was Python 3.12.9. The incompatible environment was preserved as a
timestamped backup and replaced with a clean Python 3.12.9 environment from
`requirements-dev.txt`. Repository helpers, all 86 tests, the smoke workflow,
and the security gate now run successfully through the project interpreter.

## Automated test inventory

| Test module | Tests | Primary scope |
|---|---:|---|
| `test_a2a.py` | 4 | Agent card, JSON-RPC validation, deterministic response, read-only behavior |
| `test_agent.py` | 7 | Bounded orchestration, AI validation, and deterministic fallback |
| `test_api_phase1.py` | 5 | Legacy compatibility endpoints |
| `test_api_workflow.py` | 10 | Incident, analysis, draft, approval, audit, and error workflow |
| `test_dashboard_client.py` | 2 | Dashboard API client behavior |
| `test_deployment.py` | 7 | Manifest, process command, production defaults, and deployment safety |
| `test_frontend.py` | 13 | Navigation, UI modules, responsive behavior, charts, exports, and assets |
| `test_integrations.py` | 4 | AWS adapter and SAP payload boundary |
| `test_inventory.py` | 9 | Inventory risk and time-phased projections |
| `test_postgres_config.py` | 8 | Backend selection, production fail-closed policy, and DSN resolution |
| `test_postgres_tools.py` | 3 | PostgreSQL scripts and secret-safe behavior |
| `test_repository_persistence.py` | 3 | State persistence and restoration |
| `test_sap_config.py` | 3 | SAP configuration validation and readiness reporting |
| `test_scenario_engine.py` | 8 | Feasibility, allocation, ranking, and reference recommendation |
| **Total** | **86** | |

## Core acceptance invariants

The test suite verifies the reference incident against fixed synthetic assumptions:

- usable inventory equals 1,800 kg;
- demand equals 50 kg/hour;
- initial cover equals 36 hours;
- baseline delay produces 60 hours of modeled downtime;
- baseline modeled exposure equals IDR 750 million;
- the recommended scenario is `SCN-TRANSFER-MKS+LOCAL-MKS`;
- the recommendation uses 1,800 kg transfer plus 1,200 kg local supply;
- recommended modeled downtime equals zero;
- recommended response cost equals IDR 45 million;
- baseline/wait scenarios cannot create a response draft;
- duplicate incident and draft requests remain idempotent;
- a requester cannot approve their own draft;
- stale or repeated decisions are rejected; and
- SAP AI failure cannot replace the deterministic recommendation.

These invariants validate implementation consistency, not the accuracy of real-world costs, demand, or lead times.

## Frontend verification

The current UI has been reviewed at desktop and responsive layouts for:

- persistent global navigation and deep links;
- executive overview and global filters;
- interactive Indonesia network map;
- incident workspace subnavigation;
- 24-hour, 72-hour, and full inventory horizons;
- chart tooltips and CSV export;
- scenario-frontier selection and detail panel;
- sortable, filterable, paginated tables;
- approval and audit workflows; and
- browser-console errors.

No errors or warnings were observed in the reviewed browser flow. This is manual evidence; a Playwright-style browser suite and visual regression pipeline are still required.

## External integration evidence

### Cloud Foundry

Public read-only checks on 2026-10-13 confirmed that the deployed route is reachable. The current runtime reports production mode but still uses SQLite with `ephemeral-instance` scope. Therefore cloud availability is verified, while durable cloud persistence is not.

### SAP AI Core

A controlled live inference was completed previously from the BTP runtime, and the deployed status records `SAP AI LIVE VERIFIED`. Public request-time inference remains disabled by policy. The deterministic fallback is covered by automated tests.

### SAP Joule

The tenant capability previously returned an NSRA incident briefing through the A2A boundary. The public agent card is currently reachable. A fresh tenant conversation should be included in every release rehearsal because Joule capability state and destination configuration are external to this repository.

### PostgreSQL

PostgreSQL code, configuration discovery, TLS verification, migration behavior, and production fail-closed rules are covered by tests. No managed database was contacted during this evaluation, and the deployed app does not yet use PostgreSQL.

### AWS

EventBridge/Lambda behavior is locally emulated and tested. No AWS account, event bus, Lambda function, IAM role, or dead-letter queue was called during this evaluation.

### SAP ERP

The adapter creates a `simulationOnly: true` payload and performs no network request. No purchase order, stock transfer, or other ERP document has been created.

## Reproduce the local evidence

After creating a healthy `.venv`:

```powershell
.\scripts\run_tests.ps1
.\scripts\security_check.ps1
.\scripts\start_demo.ps1 -NoBrowser
python scripts\demo_smoke.py
.\scripts\stop_demo.ps1
```

Expected smoke output includes:

```text
SMOKE PASS | coverage=36h | baseline_downtime=60h | recommendation=SCN-TRANSFER-MKS+LOCAL-MKS | draft=APPROVED
```

## Remaining evaluation work

- Browser automation and screenshot regression.
- Accessibility testing with keyboard and assistive technology.
- API and database load/concurrency testing.
- PostgreSQL restage, backup, and restore exercise.
- Authenticated penetration and authorization testing.
- Live AWS event and failure-path test.
- SAP read-only business-data reconciliation.
- Model calibration and historical backtesting.
- Observability, alert, and disaster-recovery exercise.
