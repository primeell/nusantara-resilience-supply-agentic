# NSRA initial architecture

## Components

- **FastAPI backend**: local API boundary for health, readiness, and later domain endpoints.
- **Agent layer**: orchestration boundary plus the SAP AI Core GPT-5.4 client.
- **Inventory and mock ERP**: deterministic local data interfaces for testing without SAP access.
- **Optimization**: small scenario-selection interface, ready to be replaced by a richer optimizer.
- **Streamlit dashboard**: local MVP view of mock inventory and stockout risk.
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

