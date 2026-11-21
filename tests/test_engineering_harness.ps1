[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$PythonExecutable)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$temporaryParent = Join-Path $root '.harness-test-tmp'
$temporaryRoot = Join-Path $temporaryParent ([guid]::NewGuid().ToString('N'))
$shell = (Get-Command powershell.exe -CommandType Application).Source
$count = 0

function Run-Process([string]$Executable, [string[]]$ProcessArguments) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Executable
    $info.Arguments = (($ProcessArguments | ForEach-Object { '"' + $_ + '"' }) -join ' ')
    $info.WorkingDirectory = $root
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $output = $process.StandardOutput.ReadToEndAsync()
        $errors = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        return [pscustomobject]@{ Code = $process.ExitCode; Text = $output.GetAwaiter().GetResult() + $errors.GetAwaiter().GetResult() }
    } finally { $process.Dispose() }
}

function Check([bool]$Condition, [string]$Name) {
    if (-not $Condition) { throw "Harness assertion failed: $Name" }
    $script:count++
    Write-Output "PASS: $Name"
}

function Run-Script([string]$Path, [string[]]$Extra = @()) {
    return Run-Process $shell (@('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Path) + $Extra)
}

function Fixture-Git([string[]]$GitArguments) {
    $result = Run-Process 'git.exe' (@('-c', "safe.directory=$temporaryRoot", '-C', $temporaryRoot) + $GitArguments)
    if ($result.Code -ne 0) { throw 'Isolated fixture Git setup failed.' }
}

try {
    $verify = Join-Path $root 'scripts\verify.ps1'
    $security = Join-Path $root 'scripts\security_check.ps1'
    $result = Run-Script $verify @('-PythonExecutable', $PythonExecutable)
    Check ($result.Code -eq 0 -and $result.Text -match 'RESULT: PASS; Tests: 98; Failures: 0; Errors: 0; Skipped: 0' -and $result.Text -match 'External-reference available: 5') 'explicit Python runs 28 readiness, 16 API, 35 mocked-provider and 19 simulator tests'
    $result = Run-Script $verify
    Check ($result.Code -eq 0 -and $result.Text -match 'RESULT: PASS; Tests: 98') 'automatic interpreter selection runs all readiness, API, mocked-provider and simulator tests'
    $result = Run-Script $verify @('-PythonExecutable', (Join-Path $root 'nonexistent-python.exe'))
    Check ($result.Code -eq 2 -and $result.Text -match 'Tests: not completed') 'invalid explicit Python fails without fallback'

    [void](New-Item -ItemType Directory -Path (Join-Path $temporaryRoot 'scripts') -Force)
    [void](New-Item -ItemType Directory -Path (Join-Path $temporaryRoot 'tests') -Force)
    Copy-Item -LiteralPath $verify -Destination (Join-Path $temporaryRoot 'scripts\verify.ps1')
    $failingTest = "import unittest`nclass DeliberateFailure(unittest.TestCase):`n    def test_failure(self):`n        self.fail('synthetic harness failure')`n"
    [IO.File]::WriteAllText((Join-Path $temporaryRoot 'tests\test_failure.py'), $failingTest)
    $result = Run-Script (Join-Path $temporaryRoot 'scripts\verify.ps1') @('-PythonExecutable', $PythonExecutable)
    Check ($result.Code -eq 1 -and $result.Text -match 'Tests: 1; Failures: 1') 'unittest failures propagate a nonzero exit'
    Remove-Item -LiteralPath (Join-Path $temporaryRoot 'tests\test_failure.py')
    $result = Run-Script (Join-Path $temporaryRoot 'scripts\verify.ps1') @('-PythonExecutable', $PythonExecutable)
    Check ($result.Code -eq 1 -and $result.Text -match 'RESULT: FAIL; Tests: 0') 'zero discovered tests cannot pass'

    Fixture-Git @('init', '-b', 'main')
    [IO.File]::WriteAllText((Join-Path $temporaryRoot 'notes.txt'), 'fictional fixture only')
    Fixture-Git @('add', '--', 'notes.txt')
    $result = Run-Script $security @('-RepositoryPath', $temporaryRoot)
    Check ($result.Code -eq 0 -and $result.Text -match 'RESULT: PASS') 'clean tracked fixture passes security check'
    $fake = 'SYNTHETIC_ONLY_' + [guid]::NewGuid().ToString('N')
    [IO.File]::WriteAllText((Join-Path $temporaryRoot 'notes.txt'), ('password = "' + $fake + '"'))
    Fixture-Git @('add', '--', 'notes.txt')
    [IO.File]::WriteAllText((Join-Path $temporaryRoot 'notes.txt'), 'clean working copy; index still has review lead')
    $result = Run-Script $security @('-RepositoryPath', $temporaryRoot)
    Check ($result.Code -eq 0 -and $result.Text -match 'RESULT: REVIEW REQUIRED' -and
           $result.Text -match '\(index\).*credential-assignment' -and -not $result.Text.Contains($fake)) 'index secret lead is review-only and value stays redacted'
    Fixture-Git @('add', '--', 'notes.txt')
    [IO.File]::WriteAllText((Join-Path $temporaryRoot 'notes.txt'), ('password = "' + $fake + '"'))
    $result = Run-Script $security @('-RepositoryPath', $temporaryRoot)
    Check ($result.Code -eq 0 -and $result.Text -match '\(working tree\).*credential-assignment' -and
           -not $result.Text.Contains($fake)) 'unstaged tracked content is scanned without value disclosure'
    [IO.File]::WriteAllText((Join-Path $temporaryRoot '.env'), 'FICTIONAL_FIXTURE_ONLY=1')
    Fixture-Git @('add', '--', '.env')
    $result = Run-Script $security @('-RepositoryPath', $temporaryRoot)
    Check ($result.Code -eq 1 -and $result.Text -match 'VIOLATION: .env \[prohibited-path-or-type\]') 'prohibited tracked filename fails security check'
    [IO.File]::WriteAllBytes((Join-Path $temporaryRoot 'fixture.joblib'), [byte[]]@())
    Fixture-Git @('add', '--', 'fixture.joblib')
    $result = Run-Script $security @('-RepositoryPath', $temporaryRoot)
    Check ($result.Code -eq 1 -and $result.Text -match 'VIOLATION: fixture.joblib \[prohibited-path-or-type\]') 'prohibited tracked model extension fails without loading content'
    $result = Run-Script $security @('-RepositoryPath', (Join-Path $temporaryRoot 'not-a-repository'))
    Check ($result.Code -eq 2) 'incomplete security inspection fails closed'
    $result = Run-Script $verify @('-PythonExecutable', $PythonExecutable, '-TestMode', 'Portable')
    Check ($result.Code -eq 0 -and $result.Text -match 'RESULT: PASS; Tests: 93; Failures: 0; Errors: 0; Skipped: 0' -and
           $result.Text -match 'External-reference excluded: 5') 'portable mode explicitly excludes five external-reference tests'
    Write-Output "HARNESS RESULT: PASS; Checks: $count"
    exit 0
} catch {
    Write-Output $_.Exception.Message
    Write-Output "HARNESS RESULT: FAIL; Completed checks: $count"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        $resolved = (Resolve-Path -LiteralPath $temporaryRoot).Path
        $boundary = [IO.Path]::GetFullPath($temporaryParent).TrimEnd('\') + '\'
        if (-not $resolved.StartsWith($boundary, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Refusing to remove a fixture outside the workspace test directory.'
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
