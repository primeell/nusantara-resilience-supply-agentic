# SAP BTP Cloud Foundry deployment

This runbook deploys NSRA without placing SAP credentials in Git, shell history,
the manifest, or command output.

> **Current deployment note (2026-10-13):** the public route is healthy, but
> `/api/v1/status` still reports SQLite with `ephemeral-instance` scope. Do not
> treat the running revision as durably deployed. Provision PostgreSQL, protect
> mutation routes, and deploy the current branch using this runbook.

## Fixed target

- API: `https://api.cf.ap10.hana.ondemand.com`
- Organization: `SEAIO_aws-sap-hackathon-si4ykj9d`
- Space: `hackathon-a-cruel-angel-s-thesis`
- App: `nsra-a-cruel-angels-thesis`

## 1. Authenticate with the hackathon identity provider

Run this yourself in an interactive PowerShell window:

```powershell
cf api https://api.cf.ap10.hana.ondemand.com
cf login `
  --origin auisywroy-platform `
  -o "SEAIO_aws-sap-hackathon-si4ykj9d" `
  -s "hackathon-a-cruel-angel-s-thesis"
```

Never paste a password, SSO passcode, OAuth token, or service-key secret into a
chat, issue, source file, or commit.

## 2. Verify entitlement and target

```powershell
cf target
cf buildpacks
cf marketplace
cf services
```

The marketplace output determines whether a PostgreSQL service can be created
in the team space. Do not guess an offering or paid plan.

## 3. Provision PostgreSQL first

The team BTP marketplace has no PostgreSQL entitlement, so use an approved
managed PostgreSQL endpoint (for example AWS RDS in the hackathon account). It
must support TLS and accept traffic from the Cloud Foundry runtime. Put its URI
only in the ignored local `.env` file:

```dotenv
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
NSRA_POSTGRES_SSLMODE=require
```

Do not commit the URI or pass it in chat. Verify it without printing the value:

```powershell
python scripts/test_postgres_connection.py
```

To preserve a reviewed local SQLite workflow, migrate it before first app
startup. The command refuses to overwrite an initialized destination unless
`--force` is supplied deliberately:

```powershell
python scripts/migrate_sqlite_to_postgres.py
```

## 4. Deploy without starting

```powershell
cd C:\nusantara-supply-agent
cf push --no-start
```

The manifest contains no credentials. The `.cfignore` file prevents local
secrets, virtual environments, local databases, tests, and development artifacts
from being uploaded.

## 5. Configure runtime values

The helper reads the approved local `.env`, sends only the required settings to
the targeted app, and prints variable names only:

```powershell
python scripts/configure_cf_runtime.py
```

Configure PostgreSQL before starting the new revision:

```powershell
python scripts/configure_postgres_runtime.py
```

Run the SAP helper without `--start`, then restage once after both helpers have
completed, or pass `--start` only to the last helper.

If `cf` is not yet visible on `PATH`, pass the exact executable with `--cf`.

## 6. Verify the deployed application

```powershell
cf app nsra-a-cruel-angels-thesis
cf logs nsra-a-cruel-angels-thesis --recent
```

Verify these HTTPS routes:

- `/health`
- `/api/v1/status`
- `/api/v1/integrations/health`
- `/overview`
- `/network`
- `/incidents`

The status response must report `SAP AI LIVE VERIFIED` only after a successful
controlled call. It must never return credentials.

Production disables public on-demand SAP AI requests by default after the live
verification. This prevents unauthenticated visitors from spending the team's AI
quota. The deterministic engine remains available to all demo users.

## Persistence policy

Local development explicitly uses SQLite. The production manifest sets
`NSRA_STATE_BACKEND=postgresql`, so deployment fails closed when neither
`DATABASE_URL`, `POSTGRES_URL`, nor a compatible bound service is present. The
public status endpoint must report `engine: postgresql`, `persistent: true`, and
`scope: durable-cloud` after deployment. Keep the app at one instance while the
snapshot repository uses its current process-level write lock.

## Joule gate

The NSRA A2A endpoint is available at `/.well-known/agent.json` and `/a2a`.
Create or update the BTP destination with:

```powershell
python scripts/configure_destination.py --cf <path-to-cf.exe>
```

The helper uses the locally stored Destination service key only in memory and
does not print it. The Joule capability is in `joule/nsra_supply_resilience`.
Joule authentication must be performed interactively by the account owner;
credentials must not be committed or passed through chat.
