# Nusantara Supply Resiliency Agent (NSRA)

Nusantara Supply Resiliency Agent (NSRA) is an agentic AI platform designed to identify maritime supply-chain disruptions in Indonesia, assess factory stockout risks, simulate alternative logistics strategies, and prepare mitigation actions through SAP integration.

Built for the **SAP–AWS Agentic AI Hackathon 2026**.

## Team

**A Cruel Angel's Thesis**

- Team slug: `a-cruel-angel-s-thesis`
- Track: Intelligent Supply Chain

## Quick Start (Windows PowerShell)

The complete local application runs offline with a versioned reference dataset.
SAP and AWS credentials are not required for the deterministic workflow.

~~~powershell
cd C:\nusantara-supply-agent
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
.\scripts\demo_doctor.ps1
.\scripts\run_tests.ps1
.\scripts\security_check.ps1
.\scripts\start_demo.ps1
~~~

Application: **http://127.0.0.1:8000**

OpenAPI: **http://127.0.0.1:8000/docs**

To stop the local services:

~~~powershell
.\scripts\stop_demo.ps1
~~~

Direct server alternative:

~~~powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
~~~

Full workflow smoke test: **python scripts/demo_smoke.py**

See the [API contract](docs/API_CONTRACT.md), [architecture](docs/architecture.md),
[demo script](docs/DEMO_SCRIPT.md), and [integration status](docs/INTEGRATION_STATUS.md).

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

This repository provides a complete local hackathon workflow:

- Versioned FastAPI incident, inventory, shipment, analysis, scenario, draft,
  decision, audit, and reset endpoints.
- Hourly deterministic stockout, recovery, unmet-demand, cost, and feasibility
  calculations.
- Bounded mitigation search with material, unit, destination, source capacity,
  MOQ, dispatch cutoff, lead-time, availability, and reliability constraints.
- Five reproducible incident fixtures with SQLite for isolated local development
  and PostgreSQL for durable cloud state.
- Allowlisted Python-driven planner, optional grounded SAP AI explanation,
  strict validation, and deterministic offline fallback.
- Human approval and audit trail; no real ERP write is possible.
- Responsive English-language control tower served directly by FastAPI, with
  real deep-linked modules for executive overview, geographic supply network,
  incident portfolio/workspaces, scenario intelligence, approval inbox, audit
  explorer, and integration health.
- Accessible operational visualizations for hourly baseline/recommended
  inventory, safety-stock and stockout windows, cost/downtime frontier,
  mitigation composition, facility-material risk, impact chain, and network and
  approval trends.
- EventBridge/Lambda-compatible local adapter and simulated SAP draft payload.
- Unit, contract, API, persistence, fallback, and mock end-to-end tests.

AWS is locally emulated, SAP AI Core live inference has been verified with a
controlled GPT-5.4 call, Joule is not yet deployed, and production SAP
transactions are intentionally not implemented.

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
- Standards-based HTML, CSS, and JavaScript frontend (no build step)
- Streamlit legacy interface retained for compatibility, not launched by default
- SAP AI Core / Generative AI Hub
- GPT-5.4
- AWS EventBridge and Lambda — planned
- PostgreSQL via an approved managed cloud endpoint
- SAP BTP Cloud Foundry
- SAP Joule A2A capability

Cloud Foundry deployment assets are included. See the
[deployment runbook](docs/CLOUD_DEPLOYMENT.md). The production manifest now
fails closed unless a PostgreSQL DSN is configured; it no longer falls back to
ephemeral SQLite in the cloud.

## Project Structure

```text
nusantara-supply-agent/
├── agent/                 # Agent orchestration and SAP AI Core client
├── backend/               # FastAPI API, inventory, optimization, mock ERP
├── frontend/              # Primary first-party operations control tower
├── integrations/          # SAP and AWS integration boundaries
├── dashboard/             # Legacy Streamlit interface and API client
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

This project supports Python `3.11` to `3.13`.

If your `.venv` was created with a different Python version than the one you want to use now, delete and recreate the virtual environment before reinstalling dependencies. This avoids mixed interpreter and package state.

Example rebuild on Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
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
SAP_GPT_DEPLOYMENT_ID=
SAP_CLAUDE_DEPLOYMENT_ID=

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
<provided through the approved private channel>

GPT-5.4 deployment:
<set SAP_GPT_DEPLOYMENT_ID locally>

Claude deployment:
<set SAP_CLAUDE_DEPLOYMENT_ID locally if used>
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

## Running the Application

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The web application and API share one origin, so
there is no second frontend process, CORS configuration, or JavaScript build
step. Business calculations remain exclusively in the Python service layer.

Primary application routes:

- `/overview` — executive portfolio and trend view
- `/network` — facilities, warehouses, ports, and inter-island routes
- `/incidents` and `/incidents/{incident_id}` — portfolio and incident workspace
- `/scenarios/{analysis_id}` — focused scenario comparison
- `/approvals` — response-package decision inbox
- `/audit` — traceable system and human activity
- `/integrations` — honest local/live/emulated integration boundaries

## Running Tests

```powershell
python -m pytest
python scripts/check_environment.py
python -m pip check
```

`check_environment.py` prints only safe diagnostics such as Python version, whether a virtual environment is active, whether `.env` exists locally, and whether required packages are importable.

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

## Post-demo Backlog

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

## Post-hackathon Roadmap

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

This project is a locally deployable decision-support MVP for the hackathon.

Implemented:

- Resettable synthetic dataset with five incident scenarios.
- Deterministic time-phased stockout and scenario engine.
- Full local API workflow through draft approval and audit.
- Bounded agent tools, grounded decision schema, and offline fallback.
- SAP AI Core client with sanitized errors and timeouts.
- EventBridge-compatible local adapter.
- FastAPI-hosted responsive operations control tower.
- Windows launch, stop, test, event simulation, and smoke scripts.
- Automated tests and security checks.

Not yet implemented:

- Live SAP inference verification in this build session.
- Production SAP business-data/write integration.
- Live or real-time maritime data.
- Provisioned AWS resources.
- Cloud Foundry deployment.
- SAP Joule deployment.
- Production-grade persistence, authentication, and authorization.

Automatic operational execution is intentionally out of scope; human approval
must never silently become a real purchase or inventory movement.

## License

This repository is currently intended for the SAP–AWS Agentic AI Hackathon 2026 and internal team development.

A formal open-source license can be added after the team agrees on distribution terms.

## Disclaimer

NSRA is a prototype for decision support. Its recommendations must be reviewed by qualified supply-chain personnel before any operational action is taken.
