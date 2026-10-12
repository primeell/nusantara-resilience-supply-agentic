$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Virtual environment not found. Run the README setup commands first.'
}

Push-Location $projectRoot
try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check_secrets.ps1
    if ($LASTEXITCODE -ne 0) {
        throw 'Secret scan failed.'
    }

    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) {
        throw 'Dependency consistency check failed.'
    }

    # Audit the already-resolved project environment. Auditing requirements.txt
    # directly makes pip-audit create a temporary virtual environment and
    # bootstrap pip/setuptools/wheel, which is slower and prone to transient
    # package-index failures on Windows.
    & $pythonPath -m pip_audit --local --progress-spinner off --timeout 30
    if ($LASTEXITCODE -ne 0) {
        throw 'Dependency vulnerability audit failed. Review the pip-audit output above.'
    }

    Write-Host 'Repository security checks passed.' -ForegroundColor Green
}
finally {
    Pop-Location
}
