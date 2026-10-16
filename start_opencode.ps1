# Run in the project root. The loopback bridge must already be running in
# another terminal.
$ErrorActionPreference = 'Stop'

if (!(Test-Path -LiteralPath '.env')) {
    throw 'Missing .env. Create it from .env.example and add the approved SAP configuration.'
}
if (!(Test-Path -LiteralPath 'opencode.json')) {
    throw 'Missing opencode.json. Run: Copy-Item .\opencode.example.json .\opencode.json'
}

$line = Get-Content -LiteralPath '.env' |
    Where-Object { $_ -match '^NSRA_PROXY_KEY=' } |
    Select-Object -Last 1
if (!$line) { throw 'NSRA_PROXY_KEY is missing. Run .\setup_proxy_key.ps1 first.' }

$env:NSRA_PROXY_KEY = $line.Substring('NSRA_PROXY_KEY='.Length).Trim()
if (!$env:NSRA_PROXY_KEY) { throw 'NSRA_PROXY_KEY is empty. Run .\setup_proxy_key.ps1 again.' }
$env:OPENCODE_CONFIG = (Resolve-Path -LiteralPath '.\opencode.json').Path

$models = & opencode models sap-local
if ($LASTEXITCODE -ne 0) {
    throw 'OpenCode could not load the sap-local provider. Validate opencode.json and the installed OpenCode version.'
}
if (-not ($models -match 'sap-local/sap-gpt54')) {
    throw 'Model sap-local/sap-gpt54 is unavailable. Recreate opencode.json from opencode.example.json.'
}

$models | Where-Object { $_ -match 'sap-local/sap-gpt54' }
Write-Host 'OpenCode configuration loaded for this terminal.'
Write-Host 'Test with: opencode run --model sap-local/sap-gpt54 "Reply with exactly: SAP_CONNECTION_OK"'
