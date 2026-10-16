# Operations guide

This runbook explains how to set up, start, stop, restart, validate, and troubleshoot NSRA from Windows PowerShell. Run commands from the repository root unless a section states otherwise.

## Command conventions

- Commands beginning with `./scripts` or `.\scripts` are repository-owned helpers.
- Repository helpers select `.venv\Scripts\python.exe` directly; activating the
  environment is optional for normal start, stop, test, and security commands.
- Manual Python commands use `.\.venv\Scripts\python.exe -m ...` explicitly so
  PowerShell cannot accidentally select `pip` or Python from another installation.
- A command that includes `--live`, `cf`, a database URL, or SAP credentials may reach an external service.
- Never paste `.env`, service-key output, passwords, tokens, or a PostgreSQL DSN into source control, issues, or chat.

## First-time local setup

```powershell
Set-Location C:\nusantara-supply-agent
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

| Command | Function |
|---|---|
| `Set-Location C:\nusantara-supply-agent` | Makes the repository the current working directory. Relative paths in later commands depend on this. |
| `py -3.12 -m venv .venv` | Creates an isolated Python environment in `.venv`. It prevents project packages from changing the system Python installation. |
| `.\.venv\Scripts\python.exe -m pip install --upgrade pip` | Updates the package installer through the exact interpreter owned by this repository. |
| `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` | Installs runtime dependencies and development security tooling into the same interpreter. `requirements-dev.txt` includes `requirements.txt`. |
| `Copy-Item .env.example .env` | Creates the ignored local runtime configuration file. Run once; do not overwrite an existing configured `.env`. |

Activation is optional. If a developer prefers activated-shell commands and
PowerShell blocks activation, change policy only for the current process:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

`-Scope Process` means the setting disappears when that terminal closes.

## Daily local start

Use this sequence when the application is currently stopped:

```powershell
Set-Location C:\nusantara-supply-agent
.\scripts\demo_doctor.ps1
.\scripts\start_demo.ps1
```

### What each helper does

| Command | Function and expected result |
|---|---|
| `.\scripts\demo_doctor.ps1` | Checks `.venv`, core imports, seed JSON, Python syntax, frontend assets, and port 8000. It exits nonzero if a prerequisite is missing. Run it while NSRA is stopped because an occupied application port is reported as a failure. |
| `.\scripts\start_demo.ps1` | Starts Uvicorn in a hidden process, redirects logs to `.nsra-local`, polls `/health`, records process identity, opens the browser, and refuses to start on an unrelated occupied port. |

The application becomes available at:

- <http://127.0.0.1:8000/overview>
- <http://127.0.0.1:8000/docs>
- <http://127.0.0.1:8000/health>

### Start without opening a browser

```powershell
.\scripts\start_demo.ps1 -NoBrowser
```

`-NoBrowser` performs the same health-checked startup but leaves browser navigation to the operator.

### Start on another port

```powershell
.\scripts\start_demo.ps1 -BackendPort 8010
```

The port must be between 1024 and 65535 and must not already be used by another process.

## Stop and restart

### Stop

```powershell
.\scripts\stop_demo.ps1
```

The script reads `.nsra-local/demo-processes.json`, verifies that the saved process start time still matches the active process, stops only that process, and removes the process-state file. Logs and SQLite data are retained.

### Restart

```powershell
.\scripts\stop_demo.ps1
.\scripts\start_demo.ps1
```

Restart after changing Python, JavaScript, CSS, `.env`, or the active persistence configuration. The managed start script does not enable hot reload.

### Run directly for development

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

This foreground command automatically reloads source changes and prints logs in the current terminal. Stop it with `Ctrl+C`. Do not run it at the same time as `start_demo.ps1` on the same port.

## Health, status, and logs

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/status | ConvertTo-Json -Depth 6
Invoke-RestMethod http://127.0.0.1:8000/api/v1/integrations/health | ConvertTo-Json -Depth 6
Get-Content .nsra-local\backend.stderr.log -Tail 100
Get-Content .nsra-local\backend.stdout.log -Tail 100
```

| Command | Function |
|---|---|
| `/health` | Verifies that the API process and active state repository are operational. |
| `/api/v1/status` | Reports version, environment, storage engine, SAP readiness, AWS mode, and transaction safety without credential values. |
| `/api/v1/integrations/health` | Reports component-level operational, verified, emulated, or disabled states. |
| `Get-Content ... -Tail 100` | Shows the latest managed-process log lines for troubleshooting. |

## Functional verification

### End-to-end smoke test

Start NSRA first, then run:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke.py
```

The smoke test resets the synthetic workspace, verifies health, runs the primary incident analysis, checks the reference recommendation, creates and approves a simulated draft, validates audit events, and resets state again.

Keep the generated state for browser inspection with:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke.py --keep-state
```

Use a different base URL with:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke.py --base-url http://127.0.0.1:8010
```

### Reset demo state manually

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/v1/demo/reset `
  -Method Post
```

This reloads `data/demo_seed.json` and clears mutable analyses, drafts, and audit records before adding a reset audit event. Use it only in a local or explicitly disposable demo environment. The endpoint must be protected or disabled before production use.

### Emulate an AWS event

```powershell
.\.venv\Scripts\python.exe scripts\simulate_event.py
```

The script constructs an EventBridge-compatible vessel-delay event, converts it to the canonical incident schema, and posts it to the local API. It does not call AWS.

## Code quality and security checks

### Automated tests

```powershell
.\scripts\run_tests.ps1
```

This uses the repository `.venv`, disables bytecode output, and runs the complete Pytest suite without creating a cache directory.

To collect tests without executing them:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q -p no:cacheprovider
```

### Security gate

```powershell
.\scripts\security_check.ps1
```

The security helper runs three checks in order:

1. `check_secrets.ps1` scans tracked and untracked non-ignored files for sensitive filenames and token patterns.
2. `pip check` verifies that installed dependency requirements are mutually consistent.
3. `pip-audit` checks pinned runtime dependencies against known vulnerability records.

Scan only tracked files with:

```powershell
.\scripts\check_secrets.ps1 -TrackedOnly
```

Use the full security helper before every push. A vulnerability database lookup may require internet access.

### Safe environment diagnostics

```powershell
.\.venv\Scripts\python.exe scripts\check_environment.py
```

This prints the OS, Python version, virtual-environment status, `.env` presence, and required-package availability. It does not print environment variable values.

## PostgreSQL operations

### Configure local connection metadata

Add values only to the ignored `.env` file:

```dotenv
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
NSRA_POSTGRES_SSLMODE=require
```

Do not include the real URI in screenshots or command history.

### Verify connectivity and TLS

```powershell
.\.venv\Scripts\python.exe scripts\test_postgres_connection.py
```

The script opens a short connection, reads the server version, confirms TLS when required, and never prints the DSN.

### Migrate reviewed local state

Stop NSRA before migration, then run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_sqlite_to_postgres.py
```

The default source is `.nsra-local/nsra-state.sqlite3`. The script validates source tables and JSON, acquires a PostgreSQL advisory transaction lock, creates destination tables, copies state, and verifies row count. It refuses to replace an initialized destination.

`--force` deliberately replaces the destination snapshot:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_sqlite_to_postgres.py --force
```

Use `--force` only after confirming that the destination data can be replaced and a recovery point exists.

### Run the application against PostgreSQL locally

Set these ignored `.env` values:

```dotenv
APP_ENV=development
NSRA_STATE_BACKEND=postgresql
NSRA_STATE_PERSISTENCE=durable-cloud
DATABASE_URL=<private value>
NSRA_POSTGRES_SSLMODE=require
```

Then restart NSRA and verify `/api/v1/status` reports PostgreSQL.

## SAP AI Core verification

### Offline-safe configuration check

```powershell
.\.venv\Scripts\python.exe scripts\test_sap_connection.py
```

Without `--live`, this command performs no network request and reports a mock success. It is useful for confirming that the script and dependencies run, not for proving SAP connectivity.

### Controlled live inference

```powershell
.\.venv\Scripts\python.exe scripts\test_sap_connection.py --live
```

This loads credentials from the ignored `.env`, obtains an OAuth token, and makes one inference request. Use it only with authorization, expected quota, and a private terminal. A successful command is evidence for that moment and configuration; it does not enable public live inference automatically.

## Local OpenCode-to-SAP bridge

The bridge is an optional developer tool. It lets OpenCode use the team's SAP AI
Core deployment through an OpenAI-compatible loopback endpoint. It is not
required to run the NSRA web application, is not part of the Cloud Foundry
request path, and must never listen on a public interface.

### One-time workstation preparation

Confirm that `.env` already contains valid SAP AI Core configuration, then
generate a workstation-local proxy key:

```powershell
Set-Location C:\nusantara-supply-agent
.\setup_proxy_key.ps1
Copy-Item .\opencode.example.json .\opencode.json -Force
```

`setup_proxy_key.ps1` writes `NSRA_PROXY_KEY` to the ignored `.env` without
printing it. `opencode.json` is also ignored because it is local tool
configuration. Each developer generates a separate key and never shares or
commits it.

### Terminal 1: start the bridge

```powershell
Set-Location C:\nusantara-supply-agent
.\.venv\Scripts\python.exe -m uvicorn bridge.proxy:app `
  --host 127.0.0.1 `
  --port 8765 `
  --env-file .env `
  --log-level info
```

Keep this terminal open. Verify the actual health route from another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

The expected result contains `status: ok`. A browser request to `/` returns
`404 Not Found` by design; the bridge exposes `/health`, `/v1/models`, and
`/v1/chat/completions`, not a web page.

### Terminal 2: load local authentication and run OpenCode

```powershell
Set-Location C:\nusantara-supply-agent
.\start_opencode.ps1
opencode models sap-local
opencode run --model sap-local/sap-gpt54 "Reply with exactly: SAP_CONNECTION_OK"
```

`start_opencode.ps1` loads only `NSRA_PROXY_KEY` into the current PowerShell
process, sets `OPENCODE_CONFIG` to the project file, and verifies that OpenCode
can discover `sap-local/sap-gpt54`. The model identifier follows
`provider-id/model-id`; it does not need to equal the SAP deployment ID because
the bridge fixes the approved deployment server-side.

### Bridge request path and security boundary

```text
OpenCode
  -> Bearer NSRA_PROXY_KEY
  -> http://127.0.0.1:8765/v1/chat/completions
  -> bridge/proxy.py
  -> SAP OAuth client-credentials token
  -> SAP AI Core deployment
  -> streamed or JSON response back to OpenCode
```

The bridge removes the client-supplied model name and always calls the
configured `SAP_GPT_DEPLOYMENT_ID`. It hides SAP error bodies and credentials
from the client. Loopback binding and the proxy key protect the local boundary;
they do not turn the bridge into a production gateway.

## Cloud Foundry deployment

The current repository manifest requires PostgreSQL in production. Provision and test the database before deploying the current branch.

### Locate the CLI

If `cf` is not on `PATH`, define the installed executable for the current terminal:

```powershell
$cf = 'C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\CloudFoundry.CLI.v8_Microsoft.Winget.Source_8wekyb3d8bbwe\cf.exe'
```

### Authenticate and target the team space

```powershell
& $cf api https://api.cf.ap10.hana.ondemand.com
& $cf login `
  --origin auisywroy-platform `
  -o 'SEAIO_aws-sap-hackathon-si4ykj9d' `
  -s 'hackathon-a-cruel-angel-s-thesis'
& $cf target
```

- `cf api` selects the regional Cloud Foundry API.
- `cf login --origin ...` authenticates interactively through the hackathon identity provider and targets the organization and space.
- `cf target` confirms the active API, user, organization, and space.

Do not combine `--sso` and `--origin`; Cloud Foundry CLI treats them as mutually exclusive login methods. If the token has expired, run the interactive `login --origin` command again.

### Deploy and inject runtime settings

```powershell
& $cf push --no-start
.\.venv\Scripts\python.exe scripts\configure_cf_runtime.py --cf $cf
.\.venv\Scripts\python.exe scripts\configure_postgres_runtime.py --cf $cf
& $cf restage nsra-a-cruel-angels-thesis
```

| Command | Function |
|---|---|
| `cf push --no-start` | Uploads the application using `manifest.yml` but does not start it before secrets and database configuration are present. |
| `configure_cf_runtime.py` | Copies only approved SAP setting names and values from local `.env` into app environment variables; secret values are never printed. |
| `configure_postgres_runtime.py` | Configures `DATABASE_URL`, PostgreSQL backend selection, durable-cloud scope, and SSL mode without printing the DSN. |
| `cf restage` | Rebuilds/restarts the app so the newly configured environment is loaded. |

Verify the deployed revision:

```powershell
& $cf app nsra-a-cruel-angels-thesis
& $cf logs nsra-a-cruel-angels-thesis --recent
$base = 'https://nsra-a-cruel-angels-thesis.cfapps.ap10.hana.ondemand.com'
Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/api/v1/status" | ConvertTo-Json -Depth 6
```

The status gate is `engine: postgresql`, `persistent: true`, and `scope: durable-cloud`. Full deployment guidance is in [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md).

## SAP Joule and destination operations

Create or update the BTP destination after the NSRA route is healthy:

```powershell
.\.venv\Scripts\python.exe scripts\configure_destination.py --cf $cf
```

The helper retrieves the configured Destination service key through Cloud Foundry, uses it in memory to create or update `NSRA_SUPPLY_AGENT_A2A`, and does not print credential values.

Check an already authenticated Joule CLI session with:

```powershell
$joule = 'C:\Users\HP\AppData\Roaming\npm\joule.ps1'
& $joule status
```

Joule login only authenticates the CLI. A successful conversation additionally requires a deployed capability, a valid destination, a reachable NSRA A2A endpoint, and an authorized tenant identity. Follow the current participant manual for login and capability deployment because those CLI flags and tenant endpoints are environment-specific.

## Troubleshooting

### Port 8000 is already in use

First check whether NSRA already owns it:

```powershell
.\scripts\start_demo.ps1
```

The helper reports an existing managed NSRA process. If another program owns the port, use `-BackendPort 8010` or stop that program explicitly.

### The managed application does not become healthy

```powershell
Get-Content .nsra-local\backend.stderr.log -Tail 200
```

Common causes are an invalid `.env`, a stale virtual environment, missing dependencies, or an enforced PostgreSQL backend without a reachable DSN.

### The virtual environment points to a removed Python installation

Move the stale environment aside and recreate it:

```powershell
Rename-Item .venv .venv-stale
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Renaming is recoverable and avoids deleting unknown files.

### Python reports packages as unsupported on this platform

If startup fails with an import such as
`No module named 'pydantic_core._pydantic_core'`, inspect the interpreter and
installed wheels:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.version); print(sys.executable)"
.\.venv\Scripts\python.exe -m pip check
Get-ChildItem .\.venv\Lib\site-packages -Recurse -Filter '*.pyd' |
  Select-Object -ExpandProperty Name -Unique
```

For example, a Python 3.12 interpreter cannot load files tagged `cp313` because
those extensions were compiled for Python 3.13. This normally means a different
Python installation's `pip` wrote into the environment or the environment was
copied between machines or Python versions.

Preserve the broken environment, recreate it with one interpreter, and install
through that exact interpreter:

```powershell
.\scripts\stop_demo.ps1
$backupName = ".venv-broken-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Rename-Item -LiteralPath .venv -NewName $backupName
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\scripts\demo_doctor.ps1
```

If the Python launcher is unavailable, call the approved base interpreter by
its full path when creating `.venv`. Do not edit `pyvenv.cfg` or rename compiled
extension files; neither action changes their ABI.

### The bridge starts but the browser shows 404

This is expected for `http://127.0.0.1:8765/`. Verify the health route instead:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
```

The bridge intentionally has no root web page or favicon route.

### OpenCode reports `Model unavailable: sap-local/sap-gpt54`

This error occurs before a request reaches SAP. Confirm the local config and
load it into the same terminal that runs OpenCode:

```powershell
Test-Path .\opencode.json
Get-Content .\opencode.json -Raw | ConvertFrom-Json | Out-Null
.\start_opencode.ps1
opencode models sap-local
```

The model list must contain `sap-local/sap-gpt54`. If it does not, recreate the
ignored local config from the tracked current-format template:

```powershell
Copy-Item .\opencode.example.json .\opencode.json -Force
.\start_opencode.ps1
```

If OpenCode reaches the bridge, the Uvicorn terminal logs a request to
`POST /v1/chat/completions`. No POST means model/provider discovery is still the
problem. `POST /v1/responses 404` means the config is using the wrong SDK; the
tracked template deliberately uses `@ai-sdk/openai-compatible`.

### Dependency audit cannot build its temporary environment

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip wheel setuptools pip-audit
.\scripts\security_check.ps1
```

If it still fails, confirm internet access and inspect the first `pip-audit` error. Do not mark the security gate passed when the audit did not run.

### Cloud Foundry reports an expired token

Run the documented `cf login --origin ...` command again. A successful `cf target` can display the previous target even when the management token is no longer valid, so confirm with `cf app` after reauthentication.

### Joule logs in but returns no answer

Verify in this order:

1. the public `/.well-known/agent.json` route responds;
2. the `/a2a` endpoint accepts the expected JSON-RPC contract;
3. `NSRA_SUPPLY_AGENT_A2A` points to the current route;
4. the capability and scenario are deployed in the tenant; and
5. the account has permission to execute the capability.

Login success alone does not prove any of these downstream components.

### Recover local demo state without deleting it

Stop NSRA, then rename the SQLite file:

```powershell
.\scripts\stop_demo.ps1
Rename-Item .nsra-local\nsra-state.sqlite3 nsra-state.backup.sqlite3
.\scripts\start_demo.ps1
```

The application creates a fresh state store from the seed. Keep the backup until recovery is confirmed.
