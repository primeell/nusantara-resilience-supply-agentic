# Security Policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or exposed credential.
Use GitHub's private security advisory flow for this repository and include the
affected component, reproduction steps, and potential impact. Do not include
real service keys, access tokens, passwords, or production data in the report.

## Credential handling

- Keep SAP, AWS, Cloud Foundry, Joule, database, and proxy credentials outside
  the repository.
- Store local values in `.env`; commit only empty names or safe defaults in
  `.env.example`.
- Use Cloud Foundry environment variables or service bindings in deployed
  environments.
- Never commit keybroker responses, service-key exports, private certificates,
  CLI login caches, or command output containing credentials.
- Install development checks with
  `python -m pip install -r requirements-dev.txt`.
- Run `powershell -File scripts/security_check.ps1` before staging a release.
- If a credential is committed or shared, revoke and rotate it immediately;
  deleting the file in a later commit is not sufficient.

## Production boundary

NSRA's Joule capability and current ERP adapter are read-only. Human approval
must remain mandatory before any operational transaction. Public deployments
must protect ingestion and execution endpoints with authenticated requests,
authorization checks, idempotency controls, and auditable actor identities.
