# SAP BTP Cloud Foundry deployment

This runbook deploys NSRA without placing SAP credentials in Git, shell history,
the manifest, or command output.

## Fixed target

- API: `https://api.cf.ap10.hana.ondemand.com`
- Organization: `SEAIO_aws-sap-hackathon-si4ykj9d`
- Space: `hackathon-a-cruel-angel-s-thesis`
- App: `nsra-a-cruel-angels-thesis`

## 1. Authenticate with SSO

Run this yourself in an interactive PowerShell window:

```powershell
cf login `
  -a https://api.cf.ap10.hana.ondemand.com `
  --sso `
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

## 3. Deploy without starting

```powershell
cd C:\nusantara-supply-agent
cf push --no-start
```

The manifest contains no credentials. The `.cfignore` file prevents local
secrets, virtual environments, local databases, tests, and development artifacts
from being uploaded.

## 4. Configure SAP AI Core runtime values

The helper reads the approved local `.env`, sends only the required settings to
the targeted app, and prints variable names only:

```powershell
python scripts/configure_cf_runtime.py --start
```

If `cf` is not yet visible on `PATH`, pass the exact executable with `--cf`.

## 5. Verify the deployed application

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

The application selects PostgreSQL automatically from `DATABASE_URL`,
`POSTGRES_URL`, or a bound PostgreSQL service in `VCAP_SERVICES`. Without one, it
uses SQLite at `/tmp/nsra-state.sqlite3` as an explicitly reported
`ephemeral-instance` fallback. Keep the app at one instance until a durable
database is bound.

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
