# Run in C:\nusantara-supply-agent, after extracting the bridge/ folder.
if (!(Test-Path '.env')) { throw 'Missing project .env' }
$lines = Get-Content '.env'
if (($lines | Where-Object { $_ -match '^NSRA_PROXY_KEY=' }).Count -gt 0) {
    Write-Host 'NSRA_PROXY_KEY already exists. Keeping it unchanged.'
} else {
    $key = python -c 'import secrets;print(secrets.token_urlsafe(32))'
    if (!$key) { throw 'Unable to generate local proxy key' }
    Add-Content -Path '.env' -Value "NSRA_PROXY_KEY=$key"
    Write-Host 'Generated NSRA_PROXY_KEY in .env (not printed).'
}
