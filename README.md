# Nusantara Supply Resiliency Agent (NSRA)

Nusantara Supply Resiliency Agent (NSRA) is an agentic AI platform designed to identify maritime supply-chain disruptions in Indonesia, assess factory stockout risks, simulate alternative logistics strategies, and prepare mitigation actions through SAP integration.

Built for the **SAP–AWS Agentic AI Hackathon 2026**.

## Team

**A Cruel Angel's Thesis**

- Team slug: `a-cruel-angel-s-thesis`
- Track: Intelligent Supply Chain

## Project Overview

Indonesia's manufacturing supply chains are vulnerable to port congestion, vessel delays, weather disruptions, geopolitical events, and transportation bottlenecks.

NSRA helps supply-chain teams:

1. Detect potential maritime disruptions.
2. Estimate their impact on factories and materials.
3. Identify stockout risks.
4. Compare alternative logistics strategies.
5. Prepare recommended mitigation actions.
6. Keep a human decision-maker in control before execution.

## Current MVP Scope

This repository currently provides a secure local development workspace containing:

- Minimal FastAPI backend.
- SAP AI Core GPT-5.4 client interface.
- Inventory stockout-risk calculation.
- Mock ERP data source.
- Logistics scenario optimization interface.
- Streamlit dashboard shell.
- Offline SAP connection test mode.
- Secure environment-variable configuration.
- Pytest-based local verification.

AWS services, SAP BTP deployment, SAP Joule integration, and production SAP transactions are planned for later phases.

## Architecture

```text
Maritime Disruption Events
            |
            v
      FastAPI Backend
            |
            v
   NSRA Agent Orchestrator
       /            \\
      v              v
Inventory / ERP   SAP AI Core
Risk Analysis     GPT-5.4
      |              |
      v              v
Scenario         Analysis and
Optimization     Recommendations
            |
            v
     Human Approval
            |
            v
 Future SAP / AWS Actions
```

## Technology Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- HTTPX
- Pytest
- Streamlit
- SAP AI Core / Generative AI Hub
- GPT-5.4
- AWS EventBridge and Lambda — planned
- SAP BTP Cloud Foundry — planned
- SAP Joule — planned

## Project Structure

```text
nusantara-supply-agent/
├── agent/                 # Agent orchestration and SAP AI Core client
├── backend/               # FastAPI API, inventory, optimization, mock ERP
├── integrations/          # SAP and AWS integration boundaries
├── dashboard/             # Streamlit MVP dashboard
├── data/                  # Local data fixtures
├── tests/                 # Offline unit tests
├── docs/                  # Setup, architecture, and collaboration docs
├── scripts/               # Environment and SAP connection checks
├── .env.example           # Safe configuration template
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Local Installation

### Requirements

- Windows 10 or later
- Python 3.11 or later
- Git
- PowerShell
- VS Code or Kiro, optional

Check the installed tools:

```powershell
python --version
git --version
```

### Create the Virtual Environment

From the project directory:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\.venv\\Scripts\\Activate.ps1
```

### Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Configuration

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

The `.env` file must remain local and must never be committed.

Example configuration:

```env
SAP_CLIENT_ID=
SAP_CLIENT_SECRET=
SAP_AUTH_URL=
SAP_AI_API_URL=
SAP_RESOURCE_GROUP=default
SAP_GPT_DEPLOYMENT_ID=d1a82575de60e02a
SAP_CLAUDE_DEPLOYMENT_ID=dc9594f579d3e4c1

AWS_REGION=
APP_ENV=development
```

### Public SAP Hackathon Configuration

```text
Cloud Foundry organization:
SEAIO_aws-sap-hackathon-si4ykj9d

Cloud Foundry space:
hackathon-a-cruel-angel-s-thesis

Cloud Foundry API:
https://api.cf.ap10.hana.ondemand.com

SAP AI Core resource group:
default

GPT-5.4 deployment:
d1a82575de60e02a

Claude deployment:
dc9594f579d3e4c1
```

Do not place the following in GitHub:

- SAP client secrets.
- OAuth access tokens.
- SAP IAS passwords.
- Service-key JSON files.
- AWS access keys.
- Authorization headers.
- Private credential responses.

## Running the FastAPI Backend

Start the local API:

```powershell
python -m uvicorn backend.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Health Endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Configuration Status Endpoint

```http
GET /api/v1/status
```

This endpoint exposes only non-sensitive readiness information. It never returns secrets, tokens, or private credential URLs.

## Running the Dashboard

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard currently uses deterministic mock ERP inventory data.

## Running Tests

```powershell
python -m pytest
python scripts/check_environment.py
python -m pip check
```

All tests are designed to run without SAP credentials or paid cloud access.

## SAP AI Core Connectivity

The default SAP connectivity check is offline and makes no network request:

```powershell
python scripts/test_sap_connection.py
```

After the project owner has supplied approved local configuration and explicitly authorizes a live network test:

```powershell
python scripts/test_sap_connection.py --live
```

The client:

1. Reads SAP configuration from environment variables.
2. Requests an OAuth token using client credentials.
3. Calls the configured GPT-5.4 deployment.
4. Uses the `default` AI resource group.
5. Refreshes the token once after an HTTP 401 response.
6. Handles timeouts and HTTP failures.
7. Avoids logging secrets and tokens.

The client does not silently substitute another LLM provider.

## Security Practices

- `.env` is ignored by Git.
- `.env.example` contains no secrets.
- Virtual environments are ignored.
- Credential JSON files are ignored.
- OAuth tokens are never committed.
- SAP IAS passwords are never requested.
- Each developer maintains an independent local `.env`.
- Each laptop requests its own OAuth token.
- Access tokens must never be copied between laptops.
- Team credentials should be stored in an encrypted team vault.
- No AWS or SAP resources are created automatically by this repository.

## Two-Laptop Collaboration

### Developer A

Responsible for:

- SAP AI Core integration.
- GPT-5.4 deployment handling.
- Agent orchestration.
- SAP adapter design.
- Cloud Foundry deployment planning.
- AWS integration planning.

Suggested branch: `feature/sap-agent`

### Developer B

Responsible for:

- Inventory data contracts.
- Mock ERP implementation.
- Stockout-risk analysis.
- Logistics scenario optimization.
- Initial backend endpoints.
- Dashboard data integration.

Suggested branches: `feature/inventory-optimization` and `feature/dashboard`

### Pull Request Workflow

1. Create a feature branch.
2. Make a focused change.
3. Run the test suite locally.
4. Review the diff.
5. Push the branch.
6. Open a pull request.
7. Request code review.
8. Merge only after tests and review pass.
9. Keep `main` protected.
10. Never force-push shared branches.

## Proposed Backlog

### SAP AI Core Client Hardening

- Test OAuth authentication.
- Test timeout handling.
- Test HTTP 401 token refresh.
- Verify that secrets are not present in logs.
- Sanitize all error messages.

### Inventory Event Schema

- Add material identifier.
- Add facility identifier.
- Add inventory quantity.
- Add demand rate.
- Add lead time.
- Add timestamp and source.

### Disruption-to-Stockout Workflow

- Load disruption fixtures locally.
- Identify affected materials and facilities.
- Calculate stockout risk deterministically.
- Display assumptions to the user.

### Scenario Comparison Endpoint

- Compare multiple logistics alternatives.
- Display cost and delay.
- Display assumptions.
- Record human approval status.

### Human Approval and Audit Trail

- Require explicit approval before operational actions.
- Record approved and rejected recommendations.
- Record decision-maker and timestamp.
- Prevent automatic SAP execution without authorization.

## Human-in-the-Loop Design

NSRA is designed to assist supply-chain operators, not replace them.

Before any operational action, the system should present:

- Disruption summary.
- Affected facilities.
- Affected materials.
- Estimated stockout date.
- Confidence level.
- Assumptions.
- Alternative logistics strategies.
- Cost and delay trade-offs.
- Recommended mitigation.
- Required approval.

Final operational actions should require explicit human approval and an auditable decision record.

## Roadmap

### Phase 1 — Workspace and MVP

- Local FastAPI service.
- Mock ERP data.
- Basic inventory-risk analysis.
- SAP AI Core client boundary.
- Streamlit dashboard.
- Secure configuration handling.

### Phase 2 — SAP Integration

- SAP business-data adapter.
- Real inventory and demand data.
- SAP AI Core live connectivity.
- Authentication and monitoring improvements.

### Phase 3 — Disruption Intelligence

- Maritime event ingestion.
- Port congestion data.
- Weather and vessel-delay signals.
- Impact propagation across facilities and materials.

### Phase 4 — Optimization

- Multi-modal logistics alternatives.
- Cost and service-level optimization.
- Scenario simulation.
- Explainable recommendation ranking.

### Phase 5 — Cloud Deployment

- SAP BTP Cloud Foundry deployment.
- AWS EventBridge integration.
- AWS Lambda or containerized event processing.
- Monitoring and audit logging.
- SAP Joule integration planning.

## Project Status

This project is an early-stage hackathon MVP workspace.

Implemented:

- Local development scaffold.
- Minimal backend API.
- Mock inventory data.
- Stockout-risk calculation.
- SAP AI Core client interface.
- Offline SAP connection mode.
- Streamlit dashboard shell.
- Local tests and security checks.

Not yet implemented:

- Production SAP integration.
- Real-time maritime data.
- AWS resources.
- Cloud Foundry deployment.
- SAP Joule integration.
- Automatic operational execution.
- Production-grade authentication and authorization.

## License

This repository is currently intended for the SAP–AWS Agentic AI Hackathon 2026 and internal team development.

A formal open-source license can be added after the team agrees on distribution terms.

## Disclaimer

NSRA is a prototype for decision support. Its recommendations must be reviewed by qualified supply-chain personnel before any operational action is taken.
