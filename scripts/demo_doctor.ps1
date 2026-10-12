param(
    [ValidateRange(1024, 65535)][int]$ApplicationPort = 8000
)

$ErrorActionPreference = "Continue"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Failures = 0

function Write-Check {
    param([string]$Name, [bool]$Passed, [string]$Detail)
    if ($Passed) {
        Write-Host "[PASS] $Name - $Detail" -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] $Name - $Detail" -ForegroundColor Red
        $script:Failures++
    }
}

function Test-TcpPort {
    param([int]$Port)
    $Client = [System.Net.Sockets.TcpClient]::new()
    try {
        $Result = $Client.BeginConnect("127.0.0.1", $Port, $null, $null)
        return $Result.AsyncWaitHandle.WaitOne(250) -and $Client.Connected
    }
    finally {
        $Client.Dispose()
    }
}

Write-Host "NSRA Environment Doctor"
Write-Host "Project: $ProjectRoot"

$PythonExists = Test-Path -LiteralPath $PythonPath
Write-Check "Virtual environment" $PythonExists $PythonPath

if ($PythonExists) {
    & $PythonPath -c "import fastapi, pydantic, requests, uvicorn" 2>$null
    Write-Check "Python dependencies" ($LASTEXITCODE -eq 0) "Core runtime imports"

    & $PythonPath -c "import json, pathlib; json.loads(pathlib.Path('data/demo_seed.json').read_text(encoding='utf-8'))" 2>$null
    Write-Check "Seed dataset" ($LASTEXITCODE -eq 0) "data/demo_seed.json is valid JSON"

    & $PythonPath -m compileall -q backend agent integrations dashboard 2>$null
    Write-Check "Python syntax" ($LASTEXITCODE -eq 0) "Application modules compile"
}

$FrontendFiles = @(
    (Join-Path $ProjectRoot "frontend\index.html"),
    (Join-Path $ProjectRoot "frontend\assets\styles.css"),
    (Join-Path $ProjectRoot "frontend\assets\app.js")
)
Write-Check "Product frontend" (-not ($FrontendFiles | Where-Object { -not (Test-Path -LiteralPath $_) })) "First-party web application files are present"

$ApplicationBusy = Test-TcpPort -Port $ApplicationPort
Write-Check "Application port" (-not $ApplicationBusy) $(if ($ApplicationBusy) { "$ApplicationPort is already in use" } else { "$ApplicationPort is available" })

if ($Failures -gt 0) {
    Write-Host "$Failures check(s) require attention." -ForegroundColor Yellow
    exit 1
}

Write-Host "All preflight checks passed. Start NSRA with .\scripts\start_demo.ps1" -ForegroundColor Green
