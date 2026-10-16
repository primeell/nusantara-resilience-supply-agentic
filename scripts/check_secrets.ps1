param(
    [switch]$TrackedOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repositoryRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repositoryRoot) {
    throw 'This command must run inside a Git repository.'
}

Push-Location $repositoryRoot
try {
    if ($TrackedOnly) {
        $candidateFiles = @(git ls-files)
    } else {
        $candidateFiles = @(git ls-files --cached --others --exclude-standard)
    }

    $candidateFiles = @($candidateFiles | Where-Object { $_ } | Sort-Object -Unique)
    $findings = [System.Collections.Generic.List[object]]::new()

    $forbiddenNames = @(
        '(?i)(^|/)\.env($|\.)',
        '(?i)(^|/).*service[-_]?key.*\.json$',
        '(?i)(^|/).*credentials?.*\.json$',
        '(?i)(^|/)opencode\.json($|\.)',
        '(?i)\.(pem|p12|pfx|jks|keystore)$'
    )

    $tokenRules = [ordered]@{
        AwsAccessKey = '\b(AKIA|ASIA)[A-Z0-9]{16}\b'
        GitHubToken = '\b(ghp_|github_pat_)[A-Za-z0-9_]{20,}\b'
        OpenAiKey = '\bsk-[A-Za-z0-9_-]{20,}\b'
        GoogleApiKey = '\bAIza[0-9A-Za-z_-]{30,}\b'
        SlackToken = '\bxox[baprs]-[0-9A-Za-z-]{10,}\b'
        Jwt = '\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'
        PrivateKey = '-----BEGIN [A-Z ]*PRIVATE KEY-----'
        CredentialInUrl = 'https?://[^/\s:@]+:[^@\s/]+@'
    }

    $binaryExtensions = @(
        '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2',
        '.zip', '.gz', '.tar', '.daar', '.mtar'
    )

    foreach ($relativePath in $candidateFiles) {
        if ($relativePath -eq '.env.example') {
            continue
        }

        foreach ($rule in $forbiddenNames) {
            if ($relativePath -match $rule) {
                $findings.Add([pscustomobject]@{
                    Path = $relativePath
                    Line = '-'
                    Rule = 'Forbidden sensitive filename'
                })
                break
            }
        }

        # The scanner contains token signatures as source code. Scanning those
        # definitions would report the scanner itself instead of repository data.
        if ($relativePath -eq 'scripts/check_secrets.ps1') {
            continue
        }

        $absolutePath = Join-Path $repositoryRoot $relativePath
        if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
            continue
        }

        $file = Get-Item -LiteralPath $absolutePath
        if ($file.Length -gt 2MB -or $binaryExtensions -contains $file.Extension.ToLowerInvariant()) {
            continue
        }

        $lineNumber = 0
        foreach ($line in Get-Content -LiteralPath $absolutePath -ErrorAction SilentlyContinue) {
            $lineNumber++
            foreach ($entry in $tokenRules.GetEnumerator()) {
                if ($line -match $entry.Value) {
                    $findings.Add([pscustomobject]@{
                        Path = $relativePath
                        Line = $lineNumber
                        Rule = $entry.Key
                    })
                }
            }

            if ($line -match '(?i)(client[_-]?secret|api[_-]?key|password|private[_-]?key|authorization)\s*["'']?\s*[:=]\s*["'']([^"'']{16,})["'']') {
                $value = $Matches[2]
                $isReference = $value -match '(?i)(example|placeholder|changeme|dummy|test|\$\{|\$env:|getenv|environ|credentials?\[|\{env:[A-Za-z_][A-Za-z0-9_]*\}|\{[A-Za-z_][A-Za-z0-9_]*\})'
                if (-not $isReference) {
                    $findings.Add([pscustomobject]@{
                        Path = $relativePath
                        Line = $lineNumber
                        Rule = 'Literal sensitive assignment'
                    })
                }
            }
        }
    }

    $uniqueFindings = @($findings | Sort-Object Path, Line, Rule -Unique)
    if ($uniqueFindings.Count -gt 0) {
        Write-Host 'Potential secrets found. Values are intentionally not displayed.' -ForegroundColor Red
        $uniqueFindings | Format-Table -AutoSize
        exit 1
    }

    Write-Host "Secret scan passed for $($candidateFiles.Count) repository files."
}
finally {
    Pop-Location
}
