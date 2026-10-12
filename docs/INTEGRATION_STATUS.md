# Integration status

## Status labels

| Capability | Status | Evidence |
|---|---|---|
| FastAPI deterministic workflow | LOCAL MOCK VERIFIED | Automated unit/API/end-to-end tests |
| Streamlit-to-FastAPI client | LOCAL MOCK VERIFIED | Client tests and local smoke procedure |
| SAP AI Core HTTP client | LIVE VERIFIED IN CLOUD | Controlled GPT-5.4 inference succeeded from the deployed BTP runtime on 2026-10-11; OAuth and response were validated without logging secrets |
| Deterministic AI fallback | MOCK VERIFIED | Timeout, malformed JSON, unknown evidence and changed scenario tests |
| PostgreSQL state store | IMPLEMENTED, MANAGED ENDPOINT PENDING | Production fails closed without PostgreSQL; TLS connection verification, health probing, secret-safe CF configuration, and SQLite migration tooling are implemented |
| SAP BTP Cloud Foundry app | DEPLOYED AND HEALTHY | `nsra-a-cruel-angels-thesis` runs in the team space with public `/health`, status, and integration-health verification |
| SAP transaction payload mapping | LOCAL MOCK VERIFIED | Payload is marked simulationOnly; no network write method exists |
| AWS EventBridge/Lambda contract | LOCAL EMULATED; LIVE NOT VERIFIED | Normalization and idempotent local handler tests |
| SAP Joule | LIVE VERIFIED IN TENANT | The A2A capability was deployed and returned the NSRA incident response in Joule using the authorized BTP identity |
| Real ERP order or stock transfer | INTENTIONALLY NOT IMPLEMENTED | Human approval changes local simulated state only |

## Minimal future live proof

SAP AI Core has passed the approved low-cost verification gate. AWS may be
marked live only after a permitted event is sent through an actual
EventBridge/Lambda resource and the backend receipt is recorded. Cloud Foundry
may be marked deployed only after route and health verification. Joule may be
marked deployed only after a real end user invokes it in the authorized tenant.

No unperformed cloud or transaction proof is represented as complete.
