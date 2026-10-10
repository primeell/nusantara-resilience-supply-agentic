# Collaboration and security

## Two-laptop workflow

Each developer clones the private repository into a separate local directory, creates their own `.venv`, and maintains their own ignored `.env`. Developers never copy access tokens, credential JSON, or personal SAP IAS passwords between laptops.

The team may use the same team-level SAP AI Core service credential only if the organizer explicitly permits it. Each laptop independently requests OAuth tokens at runtime. Store the service secret in an encrypted team vault with least-privilege access and audit logging; share only the minimum approved fields through the vault.

Do not generate another service key, change IAM roles, or use a personal IAS login as a workaround. Rotate the service credential if exposure is suspected.

## Branches and pull requests

Suggested branches are `feature/sap-agent`, `feature/inventory-optimization`, and `feature/dashboard`. Keep `main` protected and merge through pull requests after tests and review. Do not force-push or overwrite another developer’s work.

Developer A owns:

- SAP AI Core and Generative AI Hub integration.
- Agent orchestration and SAP adapter design.
- Cloud Foundry/AWS deployment planning.

Developer B owns:

- Inventory data contracts and mock ERP.
- Scenario optimization.
- Initial backend endpoints and dashboard inputs.

## Proposed issue backlog

These are proposed only; do not create them remotely without owner approval.

1. **Harden SAP AI Core client** — acceptance: OAuth, timeout, 401 refresh, and sanitized error tests pass against mocks.
2. **Define inventory event schema** — acceptance: schema covers material, facility, quantity, demand, lead time, timestamp, and source.
3. **Add disruption-to-stockout workflow** — acceptance: a deterministic fixture produces an explainable risk result.
4. **Add scenario comparison endpoint** — acceptance: alternatives show cost, delay, assumptions, and a human approval state.
5. **Create Cloud Foundry deployment manifest** — acceptance: deployment instructions are tested without committing credentials.
6. **Add audit trail and approval gate** — acceptance: recommendations and human decisions are traceable.

## GitHub approval gate

Before creating a remote repository or pushing:

1. Confirm the active GitHub account with the project owner.
2. Obtain explicit approval for a private repository named `nusantara-supply-agent`.
3. Scan tracked files for credentials and confirm `.env` is ignored.
4. Review the exact commit file list.
5. Create the private remote and push only after approval.

Do not invite collaborators until the owner supplies exact GitHub usernames and approves the invitations.

