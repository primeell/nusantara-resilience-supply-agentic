# Windows setup

This page is the short setup checklist. The canonical command explanations, restart procedure, database operations, Cloud Foundry steps, and troubleshooting are in [OPERATIONS.md](OPERATIONS.md).

## Prerequisites

- Windows 10 or later.
- PowerShell 5.1 or PowerShell 7+.
- Python 3.11, 3.12, or 3.13.
- Git.

## Install

```powershell
Set-Location C:\nusantara-supply-agent
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`Copy-Item` is a first-run command. Do not overwrite an existing `.env`, and never commit its contents.

If this repository was moved after `.venv` was created, recreate the virtual environment. Python virtual environments are not reliably portable between paths.

Repository helpers invoke `.venv\Scripts\python.exe` directly, so activation is
not required for normal startup. For manual commands, prefer the same explicit
interpreter path to prevent Python 3.12/3.13 binary-package mismatches.

## Verify and run

```powershell
.\scripts\demo_doctor.ps1
.\scripts\run_tests.ps1
.\scripts\security_check.ps1
.\scripts\start_demo.ps1
```

Open <http://127.0.0.1:8000/overview>. Stop the application with:

```powershell
.\scripts\stop_demo.ps1
```

SAP and PostgreSQL values are optional for the deterministic local workflow. Store them only in the ignored `.env` file when those integrations are being tested.
