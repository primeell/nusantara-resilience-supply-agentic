NSRA SAP AI CORE -> OPENCODE BRIDGE BUNDLE

Extract this directory's contents into the NSRA repository root. Then follow:
  docs\OPERATIONS.md - Local OpenCode-to-SAP bridge

One-time setup:
  .\setup_proxy_key.ps1
  Copy-Item .\opencode.example.json .\opencode.json -Force

Terminal 1:
  .\.venv\Scripts\python.exe -m uvicorn bridge.proxy:app --host 127.0.0.1 --port 8765 --env-file .env

Terminal 2:
  .\start_opencode.ps1
  opencode models sap-local
  opencode run --model sap-local/sap-gpt54 "Reply with exactly: SAP_CONNECTION_OK"

Never expose the bridge publicly or commit .env/opencode.json.
