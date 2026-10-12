# Windows setup

## 1. Prerequisites

- Windows 10 or later.
- Python 3.11 or later.
- Git.
- VS Code or Kiro (optional).
- GitHub CLI is optional and is not required for local work.

Confirm the tools from PowerShell:

```powershell
python --version
git --version
```

## 2. Create and activate the environment

From the parent workspace:

```powershell
cd .\nusantara-supply-agent
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The virtual environment is local to this project and is ignored by Git.

## 3. Configure local variables

```powershell
Copy-Item .env.example .env
```

Enter SAP values only in the local `.env`, using the team’s approved secret-delivery method. Do not request or share an SAP IAS password. Do not place access tokens, service keys, or credential JSON in the repository.

The non-secret Cloud Foundry target is:

- Cloud Foundry org: `SEAIO_aws-sap-hackathon-si4ykj9d`
- Cloud Foundry space: `hackathon-a-cruel-angel-s-thesis`
- API: `https://api.cf.ap10.hana.ondemand.com`

AI Core resource groups and deployment IDs are environment-specific. Obtain them
through the team's approved private channel and store them only in local or
platform-managed environment variables.

## 4. Run local verification

```powershell
python scripts/check_environment.py
.\scripts\run_tests.ps1
python scripts/test_sap_connection.py
```

The connection script is mock-only unless `--live` is explicitly passed. Live checks require owner approval and valid local credentials.

## 5. Run the services

For a one-command local start, run **.\scripts\start_demo.ps1**. It starts the
FastAPI service and its first-party web application, then opens the browser at
`http://127.0.0.1:8000`. Stop the saved process with
**.\scripts\stop_demo.ps1**.

With the backend running, verify the full workflow with
**python scripts/demo_smoke.py**. The smoke script resets fixtures, verifies
analysis, creates and approves a simulated draft, checks audit events, and
resets state again.

```powershell
python -m uvicorn backend.main:app --reload
```

The API exposes only readiness flags at `/api/v1/status`; it does not return secrets, tokens, or private credential URLs.
