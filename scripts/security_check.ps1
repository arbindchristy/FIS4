[CmdletBinding()]
param([string]$RepositoryPath)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$violations = New-Object 'System.Collections.Generic.List[string]'
$reviews = New-Object 'System.Collections.Generic.List[string]'

function Invoke-Git([string]$Arguments) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = 'git.exe'
    # Trust only the explicitly selected repository for this one invocation.
    $info.Arguments = '-c "safe.directory=' + $script:repository + '" -C "' + $script:repository + '" ' + $Arguments
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $text = $stdout.GetAwaiter().GetResult()
        [void]$stderr.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw 'Git inventory/content inspection failed; no Git error content printed.' }
        return $text
    } finally { $process.Dispose() }
}

function Inspect-Text([string]$Text, [string]$Label) {
    $lineNumber = 0
    foreach ($line in ($Text -split '\r?\n')) {
        $lineNumber++
        # Pattern matches are leads for review, not proof that a value is live.
        $rules = @{
            'private-key-marker' = '-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
            'provider-token-format' = '(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,})'
            'credential-assignment' = '(?i)(?:password|passwd|pwd|api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*["'']?[^\s"'']{4,}'
            'private-network-address' = '\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b'
            'database-endpoint-assignment' = '(?i)(?:server|hostname|data source|initial catalog)\s*='
        }
        foreach ($rule in ($rules.Keys | Sort-Object)) {
            if ($line -match $rules[$rule]) { $reviews.Add("$Label line $lineNumber [$rule]") }
        }
    }
}

try {
    if ([string]::IsNullOrWhiteSpace($RepositoryPath)) { $RepositoryPath = Split-Path -Parent $PSScriptRoot }
    $script:repository = (Resolve-Path -LiteralPath $RepositoryPath).Path
    $top = (Invoke-Git 'rev-parse --show-toplevel').Trim()
    if ([IO.Path]::GetFullPath($top) -ne [IO.Path]::GetFullPath($script:repository)) {
        throw 'RepositoryPath must be the Git repository root.'
    }
    $entries = @((Invoke-Git 'ls-files --stage -z') -split "`0" | Where-Object { $_ })
    $paths = New-Object 'System.Collections.Generic.HashSet[string]'
    $indexEntries = 0
    foreach ($entry in $entries) {
        if ($entry -notmatch '^(\d{6}) ([0-9a-f]+) ([0-3])\t(.+)$') { throw 'Unrecognized Git index entry.' }
        $mode = $Matches[1]; $oid = $Matches[2]; $stage = $Matches[3]; $path = $Matches[4]
        # Escaped location only: never print matched source text or secret values.
        $label = $path -replace '[\x00-\x1f\x7f]', '?'
        [void]$paths.Add($path)
        $prohibited = $path -match '(?i)(^|/)(\.venv|venv|env|__pycache__|\.aws|\.codex|\.agents|\.streamlit|node_modules|wheels|wheelhouse|build|dist|release|releases|models|pm_out|logs|secrets)(/|$)' -or
            $path -match '(?i)(^|/)(\.env(?:\..*)?|db_config[^/]*\.json|credentials[^/]*\.json|secrets\.[^/]+)$' -or
            $path -match '(?i)\.(?:pyc|pyo|whl|joblib|pkl|pickle|onnx|h5|keras|log|pem|key|pfx|p12|sqlite3?|db|parquet|feather|xlsx?|csv|tsv)$' -or
            $path -match '(?i)(?:\.local\.|\.secrets\.)' -or
            ($path.StartsWith('data/') -and $path -ne 'data/synthetic_readiness.csv')
        if ($path -eq 'data/synthetic_readiness.csv') { $prohibited = $false }
        if ($prohibited) { $violations.Add("$label [prohibited-path-or-type]"); continue }
        if ($mode -eq '120000' -or $mode -eq '160000') {
            $violations.Add("$label [symlink-or-submodule-not-scanned]"); continue
        }
        if ($stage -ne '0') { $violations.Add("$label [unmerged-index-entry]"); continue }
        $indexEntries++
        $size = [long](Invoke-Git "cat-file -s $oid").Trim()
        if ($size -gt 1MB) { $reviews.Add("$label [index-content-over-1MiB-not-scanned]") }
        else {
            $content = Invoke-Git "cat-file blob $oid"
            if ($content.Contains("`0")) { $reviews.Add("$label [binary-index-content-not-scanned]") }
            else { Inspect-Text $content "$label (index)" }
        }
        $workingPath = Join-Path $script:repository $path
        if (Test-Path -LiteralPath $workingPath -PathType Leaf) {
            $item = Get-Item -LiteralPath $workingPath -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                $violations.Add("$label [working-tree-link-not-scanned]"); continue
            }
            if ($item.Length -gt 1MB) { $reviews.Add("$label [working-content-over-1MiB-not-scanned]") }
            else {
                $content = [IO.File]::ReadAllText($workingPath)
                if ($content.Contains("`0")) { $reviews.Add("$label [binary-working-content-not-scanned]") }
                else { Inspect-Text $content "$label (working tree)" }
            }
        } else { $reviews.Add("$label [tracked-file-missing-from-working-tree]") }
    }
    Write-Output "Tracked files checked: $($paths.Count); regular index entries inspected: $indexEntries"
    Write-Output "CONFIRMED VIOLATIONS: $($violations.Count)"
    foreach ($finding in $violations) { Write-Output "VIOLATION: $finding" }
    Write-Output "MANUAL REVIEW FINDINGS: $($reviews.Count)"
    foreach ($finding in $reviews) { Write-Output "REVIEW: $finding" }
    Write-Output 'Matched values are never printed. Untracked files are outside this check; explicitly stage and review intended files before publication.'
    if ($violations.Count -gt 0) { Write-Output 'RESULT: FAIL'; exit 1 }
    if ($paths.Count -eq 0) { Write-Output 'RESULT: ERROR (no tracked files)'; exit 2 }
    if ($reviews.Count -gt 0) { Write-Output 'RESULT: REVIEW REQUIRED (no confirmed prohibited files)'; exit 0 }
    Write-Output 'RESULT: PASS'
    exit 0
} catch {
    Write-Output 'SECURITY CHECK ERROR: inspection incomplete; details suppressed to avoid exposing sensitive content.'
    exit 2
}
