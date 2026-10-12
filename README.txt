NSRA SAP AI CORE -> OPENCODE V2 BRIDGE (EXPERIMENTAL)

1. Extract the CONTENTS of nsra_sap_bridge into C:\nusantara-supply-agent (bridge/, opencode.json, files).
2. Make sure existing .env has SAP_CLIENT_ID, SAP_CLIENT_SECRET, SAP_AUTH_URL, SAP_AI_API_URL.
3. In PowerShell from project root:
   python -m pip install -r requirements-bridge.txt
   python bridge/test_sap.py
   # Continue only if HTTP 200 and meaningful response.
4. Create private loopback bridge secret:
   .\setup_proxy_key.ps1
   (or run powershell -ExecutionPolicy Bypass -File .\setup_proxy_key.ps1 if script policies block it.)
5. Terminal 1:
   python -m uvicorn bridge.proxy:app --host 127.0.0.1 --port 8765
6. Terminal 2 (new PowerShell in project root):
   .\start_opencode.ps1
   opencode models
   opencode run --model sap-local/sap-gpt54 "Reply with Hello"

Safety:
- The bridge binds only 127.0.0.1, not 0.0.0.0. Do not deploy publicly.
- Make sure .env, *.db, and local logs are excluded from git.
- This is an experimental chat-completions proxy. Streaming is byte forwarded;
  tool-calling and responses compatibility are not guaranteed for this deployment.
- The context/output limits in opencode.json are CONSERVATIVE PLACEHOLDERS,
  not confirmed deployment limits. Adjust only after verifying actual limits.
- The env provider key is consumed by OpenCode as bearer; the service key is
  held only by the local bridge. Don't share them with other users.
- The initial test calls the SAP endpoint and can consume shared team quota.
