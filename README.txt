NSRA SAP AI CORE -> OPENCODE BRIDGE (LOCAL DEVELOPER TOOL)

Canonical documentation:
  docs\OPERATIONS.md - commands and troubleshooting
  docs\SYSTEM_INTEGRATION_GUIDE.md - architecture and security boundary

Prerequisites:
  - A healthy project .venv
  - An ignored .env containing approved SAP AI Core configuration
  - OpenCode installed locally

One-time setup from C:\nusantara-supply-agent:
  .\setup_proxy_key.ps1
  Copy-Item .\opencode.example.json .\opencode.json -Force

Optional controlled SAP verification (this consumes team quota):
  .\.venv\Scripts\python.exe bridge\test_sap.py

Terminal 1 - start the loopback bridge:
  .\.venv\Scripts\python.exe -m uvicorn bridge.proxy:app --host 127.0.0.1 --port 8765 --env-file .env

Terminal 2 - load local OpenCode configuration:
  .\start_opencode.ps1
  opencode models sap-local
  opencode run --model sap-local/sap-gpt54 "Reply with exactly: SAP_CONNECTION_OK"

Safety:
  - Never bind this bridge to 0.0.0.0 or deploy it publicly.
  - Never commit .env or opencode.json.
  - Each workstation generates an independent NSRA_PROXY_KEY.
  - The bridge fixes the SAP deployment server-side and hides upstream bodies.
  - Opening http://127.0.0.1:8765/ returns 404 by design; use /health.
