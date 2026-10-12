$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateFile = Join-Path $ProjectRoot ".nsra-local\demo-processes.json"

if (-not (Test-Path -LiteralPath $StateFile)) {
    Write-Host "No saved NSRA application processes were found."
    exit 0
}

$State = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
$Targets = @(
    @{ Name = "backend"; Id = $State.backend_pid; StartedAt = $State.backend_started_at },
    @{ Name = "dashboard"; Id = $State.dashboard_pid; StartedAt = $State.dashboard_started_at }
)
foreach ($Target in $Targets) {
    if ($Target.Id) {
        $Process = Get-Process -Id $Target.Id -ErrorAction SilentlyContinue
        if (-not $Process) { continue }
        if (-not $Target.StartedAt) {
            Write-Warning "Skipped legacy process record $($Target.Id) because no start time is available for safe verification."
            continue
        }
        $ExpectedStart = [datetime]::Parse($Target.StartedAt).ToUniversalTime()
        $ActualStart = $Process.StartTime.ToUniversalTime()
        if ([math]::Abs(($ActualStart - $ExpectedStart).TotalSeconds) -le 1) {
            Stop-Process -Id $Target.Id -ErrorAction Stop
            Write-Host "Stopped NSRA $($Target.Name) process $($Target.Id)."
        }
        else {
            Write-Warning "Skipped process $($Target.Id): its start time does not match the saved NSRA process."
        }
    }
}
Remove-Item -LiteralPath $StateFile -Force
Write-Host "NSRA application stopped. Logs remain in .nsra-local for troubleshooting."
