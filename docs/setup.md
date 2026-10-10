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

The verified public configuration is:

- Cloud Foundry org: `SEAIO_aws-sap-hackathon-si4ykj9d`
- Cloud Foundry space: `hackathon-a-cruel-angel-s-thesis`
- API: `https://api.cf.ap10.hana.ondemand.com`
- AI Core resource group: `default`
- GPT-5.4 deployment: `d1a82575de60e02a`
- Claude deployment: `dc9594f579d3e4c1`

## 4. Run local verification

```powershell
python scripts/check_environment.py
python -m pytest
python scripts/test_sap_connection.py
```

The connection script is mock-only unless `--live` is explicitly passed. Live checks require owner approval and valid local credentials.

## 5. Run the services

```powershell
python -m uvicorn backend.main:app --reload
python -m streamlit run dashboard/app.py
```

The API exposes only readiness flags at `/api/v1/status`; it does not return secrets, tokens, or private credential URLs.

