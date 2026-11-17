[CmdletBinding()]
param([Alias('PythonPath')][string]$PythonExecutable)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Invoke-PythonCode([string]$Executable, [string]$Code) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $Executable
    $info.Arguments = '-B -'
    $info.WorkingDirectory = $projectRoot
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $process.StandardInput.Write($Code)
        $process.StandardInput.Close()
        $process.WaitForExit()
        return [pscustomobject]@{
            Code = $process.ExitCode
            Output = $stdout.GetAwaiter().GetResult()
            ErrorOutput = $stderr.GetAwaiter().GetResult()
        }
    } finally { $process.Dispose() }
}

try {
    $probe = "import sys, json, unittest, pandas, numpy; print(json.dumps({'executable': sys.executable}))"
    $explicit = $PSBoundParameters.ContainsKey('PythonExecutable')
    if ($explicit -and [string]::IsNullOrWhiteSpace($PythonExecutable)) {
        throw 'The explicitly supplied Python executable is empty.'
    }
    $candidates = @()
    if ($explicit) { $candidates = @($PythonExecutable) }
    else {
        if ($env:FIS4_PYTHON) { $candidates += $env:FIS4_PYTHON }
        $candidates += Join-Path $projectRoot '.venv\Scripts\python.exe'
        $candidates += Join-Path $projectRoot 'venv\Scripts\python.exe'
        # Reuse the audited laptop environment; do not copy or modify it.
        $candidates += Join-Path (Split-Path -Parent $projectRoot) 'fleet_cpi_suite\venv\Scripts\python.exe'
        $command = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue
        if ($command) { $candidates += $command.Source }
    }
    $selected = $null
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        try {
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw 'Not a file.' }
            $result = Invoke-PythonCode $candidate $probe
            if ($result.Code -ne 0) { throw 'Python dependency probe failed.' }
            $identity = $result.Output.Trim() | ConvertFrom-Json
            $selected = $identity.executable
            break
        } catch {
            if ($explicit) { throw 'Explicit Python is unavailable or cannot import unittest, pandas, and numpy.' }
            Write-Output 'Skipping an unavailable or incompatible Python candidate.'
        }
    }
    if (-not $selected) { throw 'No usable Python found. Supply -PythonExecutable with an existing pandas/numpy environment.' }
    Write-Output "Python executable: $selected"
    Write-Output "Test directory: $(Join-Path $projectRoot 'tests')"
    $testCode = @'
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
root = Path.cwd()
sys.path.insert(0, str(root))
try:
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and result.testsRun > 0
    print('FIS4_TEST_RESULT=' + json.dumps({
        'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skipped': len(result.skipped), 'passed': passed
    }))
    sys.exit(0 if passed else 1)
except Exception as error:
    print('Verification could not complete: ' + type(error).__name__, file=sys.stderr)
    sys.exit(2)
'@
    $result = Invoke-PythonCode $selected $testCode
    if ($result.ErrorOutput) { Write-Output $result.ErrorOutput.TrimEnd() }
    $summaryLine = @($result.Output -split '\r?\n' | Where-Object { $_.StartsWith('FIS4_TEST_RESULT=') })
    if ($summaryLine.Count -ne 1) { throw 'Python did not return a valid test summary.' }
    $summary = $summaryLine[0].Substring('FIS4_TEST_RESULT='.Length) | ConvertFrom-Json
    $outcome = if ($result.Code -eq 0 -and $summary.passed) { 'PASS' } else { 'FAIL' }
    Write-Output "RESULT: $outcome; Tests: $($summary.tests); Failures: $($summary.failures); Errors: $($summary.errors); Skipped: $($summary.skipped)"
    if ($outcome -eq 'PASS') { exit 0 }
    exit 1
} catch {
    Write-Output "VERIFICATION ERROR: $($_.Exception.Message)"
    Write-Output 'RESULT: FAIL; Tests: not completed'
    exit 2
}
