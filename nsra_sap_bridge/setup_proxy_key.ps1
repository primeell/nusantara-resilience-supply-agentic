# Run from the repository root after extracting this bundle.
$ErrorActionPreference = 'Stop'

if (!(Test-Path -LiteralPath '.env')) { throw 'Missing project .env' }
if (!(Test-Path -LiteralPath '.\.venv\Scripts\python.exe')) {
    throw 'Missing project virtual environment. Complete the README setup first.'
}

$lines = @(Get-Content -LiteralPath '.env')
$existing = @($lines | Where-Object { $_ -match '^NSRA_PROXY_KEY=' })
if ($existing.Count -gt 0) {
    $current = $existing[-1].Substring('NSRA_PROXY_KEY='.Length).Trim()
    if ($current) {
        Write-Host 'NSRA_PROXY_KEY already exists. Keeping it unchanged.'
        exit 0
    }
    $lines | Where-Object { $_ -notmatch '^NSRA_PROXY_KEY=' } |
        Set-Content -LiteralPath '.env' -Encoding utf8
}

$key = & '.\.venv\Scripts\python.exe' -c 'import secrets; print(secrets.token_urlsafe(32))'
if (!$key) { throw 'Unable to generate local proxy key' }
Add-Content -LiteralPath '.env' -Value "NSRA_PROXY_KEY=$key"
Write-Host 'Generated NSRA_PROXY_KEY in .env (not printed).'
