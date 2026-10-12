# Team tasks and ownership

Team: **A Cruel Angel's Thesis** — two developers. Remote issue/branch creation
tetap dilakukan manual setelah review owner.

| Priority | Owner | Ticket | Files | Dependency | Acceptance check |
|---|---|---|---|---|---|
| P0 | Developer 1 | Agent orchestration review | agent/, tests/test_agent.py | Stable schemas | Tool allowlist, grounded schema, timeout/invalid-output fallback tests pass |
| P0 | Developer 2 | Engine assumption review | backend/inventory.py, backend/optimization.py, data/demo_seed.json | API contract | Exact 36h coverage, 60h baseline outage, feasibility and conservation tests pass |
| P0 | Shared | Contract and release review | backend/schemas.py, backend/api.py, docs/API_CONTRACT.md | Both P0 reviews | OpenAPI loads; API tests and smoke workflow pass |
| P0 | Shared | Demo rehearsal | dashboard/, scripts/, docs/DEMO_SCRIPT.md | Release review | Fresh reset completes the 3–5 minute flow without code edits |
| P1 | Developer 1 | Controlled SAP AI live verification | agent/sap_ai_client.py, docs/EVALUATION.md | Owner authorization and valid local config | One low-cost call succeeds, no secret in output, result labeled LIVE VERIFIED |
| P1 | Developer 1 | AWS live event proof | integrations/aws_events.py | Explicit cloud authorization | One permitted event reaches backend with evidence; otherwise retain LOCAL EMULATED label |
| P1 | Developer 2 | Calibrate real historical CSV | data/, validation script | Approved data source and units | Provenance, schema, unit checks, and anonymization documented |
| P2 | Shared | Persistent demo store decision | repository implementation | Post-hackathon requirements | SQLite migration plan and concurrency behavior reviewed before replacing in-memory store |
| P2 | Developer 1 | Joule capability feasibility | docs/INTEGRATION_STATUS.md | Tenant permission and product docs | End-user invocation proven before any deployed claim |

## Branch guidance

- Developer 1: feature/agent-orchestration
- Developer 2: feature/supply-chain-engine
- Shared changes: short-lived branch, both developers review before merge.

Do not force-push shared branches. Contracts, credential handling, backend entry
point, approval policy, and launch scripts require human review. This repository
session does not commit, push, merge, deploy, or invite collaborators.
