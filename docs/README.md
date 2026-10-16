# NSRA documentation

This directory separates operational guidance, implementation evidence, architecture, and future work so that the root README remains a concise project entry point.

## Recommended reading order

1. [Root README](../README.md) — product purpose, quick start, safety boundary, and documentation map.
2. [Implementation Progress](IMPLEMENTATION_PROGRESS.md) — what is complete, what is deployed, and what remains unverified.
3. [Architecture](architecture.md) — internal components, trust boundaries, deterministic engine, and persistence model.
4. [System Integration Guide](SYSTEM_INTEGRATION_GUIDE.md) — detailed service responsibilities and end-to-end SAP, AWS, Joule, database, and OpenCode flows.
5. [Integration Status](INTEGRATION_STATUS.md) — current evidence, operating policy, and verified versus pending boundaries.
6. [API Contract](API_CONTRACT.md) — endpoints, schemas, workflow state, and error behavior.
7. [Operations Guide](OPERATIONS.md) — exact PowerShell commands, their functions, validation, restart, bridge operation, and troubleshooting.
8. [Cloud Deployment](CLOUD_DEPLOYMENT.md) — secure BTP Cloud Foundry deployment and runtime gates.
9. [Evaluation](EVALUATION.md) — reproducible quality evidence and known verification limitations.
10. [Roadmap](ROADMAP.md) — prioritized path from the current prototype to a production-grade implementation.

## Reference documents

| Document | Source-of-truth scope |
|---|---|
| [Architecture](architecture.md) | Domain boundaries, data flow, persistence model, optimizer, and trust boundaries |
| [System Integration Guide](SYSTEM_INTEGRATION_GUIDE.md) | Component catalog, deployment topology, SAP/AWS service functions, OpenCode bridge, and failure isolation |
| [API Contract](API_CONTRACT.md) | HTTP endpoints, payloads, state transitions, and error behavior |
| [Cloud Deployment](CLOUD_DEPLOYMENT.md) | Secure Cloud Foundry deployment and runtime configuration |
| [Evaluation](EVALUATION.md) | Reproducible quality evidence, test coverage, and verification limitations |
| [Demo Script](DEMO_SCRIPT.md) | Five-minute presentation flow and offline fallback |
| [Collaboration](collaboration.md) | Branching, review, and team conventions |
| [Team Tasks](TEAM_TASKS.md) | Work ownership and coordination notes |

## Status vocabulary

The project uses explicit labels to avoid presenting configuration or mock behavior as a live production integration.

| Label | Meaning |
|---|---|
| **Implemented** | Code exists in the repository and is covered by relevant checks. |
| **Local verified** | The behavior has been executed successfully against local deterministic data. |
| **Live verified** | A real external service call completed successfully and evidence was reviewed. |
| **Deployed** | A runtime is reachable, but this does not imply every integration is live. |
| **Emulated** | The production contract is represented locally without calling the external platform. |
| **Pending** | Required code, access, infrastructure, or evidence is not yet complete. |
| **Disabled** | The boundary intentionally rejects or avoids external side effects. |

## Maintenance rule

Update `IMPLEMENTATION_PROGRESS.md`, `INTEGRATION_STATUS.md`, and `EVALUATION.md` together whenever a deployment, data source, or external integration changes. Never mark an integration **live verified** based only on credentials, configuration fields, a UI badge, or a successful login.
