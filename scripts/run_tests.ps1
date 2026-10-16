$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Virtual environment not found. Run the README setup commands first."
}

$env:PYTHONDONTWRITEBYTECODE = "1"
$TestExitCode = 0
Push-Location $ProjectRoot
try {
    & $PythonPath -B -m pytest -q -p no:cacheprovider
    $TestExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($TestExitCode -ne 0) {
    exit $TestExitCode
}
