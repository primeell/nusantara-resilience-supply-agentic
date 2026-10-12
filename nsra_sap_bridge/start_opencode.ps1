# Run in the project root. Proxy must already be running in another terminal.
if (!(Test-Path '.env')) { throw 'Missing .env' }
$line = Get-Content '.env' | Where-Object { $_ -match '^NSRA_PROXY_KEY=' } | Select-Object -Last 1
if (!$line) { throw 'Run setup_proxy_key.ps1 first' }
$env:NSRA_PROXY_KEY = $line.Substring('NSRA_PROXY_KEY='.Length).Trim()
if (!$env:NSRA_PROXY_KEY) { throw 'NSRA_PROXY_KEY empty' }
opencode models | Select-String 'sap-local'
Write-Host 'Test with: opencode run --model sap-local/sap-gpt54 "Reply with Hello"'
