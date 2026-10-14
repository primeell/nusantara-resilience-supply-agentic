# Team tasks and ownership

**Team:** A Cruel Angel's Thesis

**Planning source:** [ROADMAP.md](ROADMAP.md)

This file converts the product roadmap into a practical two-developer work split. Owners can be changed during planning; acceptance criteria should not be weakened without review.

## Current release tasks

| Priority | Suggested owner | Work item | Main scope | Acceptance check |
|---|---|---|---|---|
| P0 | Shared | Provision managed PostgreSQL | Cloud account, `.env`, deployment runtime | TLS connection succeeds; secrets remain private |
| P0 | Developer 1 | Configure Cloud Foundry runtime | `manifest.yml`, deployment scripts, BTP | App reports `postgresql` and `durable-cloud` |
| P0 | Developer 2 | Validate state migration | Repository, migration tool, workflow | State survives restage and row counts reconcile |
| P0 | Shared | Protect mutation routes | Authentication, roles, reset policy | Anonymous mutation is denied; planner cannot self-approve |
| P0 | Shared | Deploy and rehearse current UI | Frontend, API, demo script | Current navigation/charts run on the public revision |
| P1 | Developer 1 | Harden Joule A2A access | Destination, A2A, tenant capability | Authenticated tenant call succeeds after redeploy |
| P1 | Developer 1 | Deploy AWS event path | EventBridge, Lambda, IAM, DLQ | One live event creates exactly one incident |
| P1 | Developer 2 | Prepare governed historical extracts | Data contracts and validation | Provenance, units, anonymization, and quality report pass |
| P1 | Developer 2 | Add browser automation | UI and test pipeline | Critical desktop/mobile workflows pass unattended |
| P1 | Shared | Add observability and CI gates | Logs, metrics, alerts, pipeline | Release is blocked on failed tests/security checks |
| P2 | Shared | Calibrate and backtest optimizer | Engine, data, evaluation | Results are compared with historical outcomes |
| P2 | Shared | Design controlled ERP writeback | SAP adapter, approval, audit | Sandbox-only, idempotent, authenticated flow is approved |

## Working agreement

- Create a short-lived branch for one coherent change.
- Run tests and the security gate before opening a pull request.
- Require review for schemas, approval policy, credential handling, deployment files, and integration behavior.
- Keep external-integration evidence in `INTEGRATION_STATUS.md` and test evidence in `EVALUATION.md`.
- Never label an integration live based only on configuration or login success.
- Do not force-push a shared branch or commit secrets.

## Release review checklist

- [ ] All automated tests pass.
- [ ] Secret scan, dependency consistency, and vulnerability audit pass.
- [ ] Smoke workflow passes from a clean reset.
- [ ] `/api/v1/status` reports the intended storage and integration policy.
- [ ] The application survives a restart/restage without losing required state.
- [ ] Joule and any live integration are reverified after deployment.
- [ ] Documentation status and evidence dates are updated.
