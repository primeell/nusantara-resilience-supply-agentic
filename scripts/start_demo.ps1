param(
    [ValidateRange(1024, 65535)][int]$BackendPort = 8000,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$StateDirectory = Join-Path $ProjectRoot ".nsra-local"
$StateFile = Join-Path $StateDirectory "demo-processes.json"
$BackendOutLog = Join-Path $StateDirectory "backend.stdout.log"
$BackendErrorLog = Join-Path $StateDirectory "backend.stderr.log"

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

function Wait-HttpReady {
    param([string]$Uri, [int]$Attempts = 30)
    for ($Attempt = 1; $Attempt -le $Attempts; $Attempt++) {
        try {
            $Response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 2
            if ($Response.StatusCode -eq 200) { return $true }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Virtual environment not found. Run the README setup commands first."
}

New-Item -ItemType Directory -Force -Path $StateDirectory | Out-Null

if (Test-Path -LiteralPath $StateFile) {
    $Saved = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
    $BackendProcess = Get-Process -Id $Saved.backend_pid -ErrorAction SilentlyContinue
    if ($BackendProcess) {
        Write-Host "NSRA is already running."
        Write-Host "Application: http://127.0.0.1:$($Saved.backend_port)"
        Write-Host "API docs:    http://127.0.0.1:$($Saved.backend_port)/docs"
        exit 0
    }
    Remove-Item -LiteralPath $StateFile -Force
}

if (Test-TcpPort -Port $BackendPort) {
    throw "Application port $BackendPort is already in use. Choose another port with -BackendPort."
}

$BackendArguments = @(
    "-m", "uvicorn", "backend.main:app",
    "--host", "127.0.0.1",
    "--port", $BackendPort.ToString()
)
$Backend = Start-Process -FilePath $PythonPath -ArgumentList $BackendArguments `
    -WorkingDirectory $ProjectRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $BackendOutLog -RedirectStandardError $BackendErrorLog

$BackendHealth = "http://127.0.0.1:$BackendPort/health"
if (-not (Wait-HttpReady -Uri $BackendHealth)) {
    Stop-Process -Id $Backend.Id -ErrorAction SilentlyContinue
    throw "Application did not become healthy. Review $BackendErrorLog."
}

@{
    backend_pid = $Backend.Id
    backend_started_at = $Backend.StartTime.ToString("o")
    backend_port = $BackendPort
    project_root = $ProjectRoot
} | ConvertTo-Json | Set-Content -LiteralPath $StateFile -Encoding UTF8

Write-Host "NSRA is ready."
Write-Host "Application: http://127.0.0.1:$BackendPort"
Write-Host "API docs:    http://127.0.0.1:$BackendPort/docs"
Write-Host "Logs:        $StateDirectory"
Write-Host "Stop:        .\scripts\stop_demo.ps1"

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$BackendPort"
}
