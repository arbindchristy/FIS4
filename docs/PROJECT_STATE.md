# FIS4 project state

## Baseline

Phase 01 readiness baseline: **PASS**, 28 tests, zero failures/errors/skips.
Published GitHub baseline: [`a57936a8fff7e0502bceef008ea609fe4aef7379`](https://github.com/arbindchristy/FIS4/commit/a57936a8fff7e0502bceef008ea609fe4aef7379)
on `main` in the private `arbindchristy/FIS4` repository. The earlier publication
verified that local HEAD, origin/main, and the GitHub commit matched. This phase
does not contact GitHub or re-verify current remote state.

`TEST_REPORT.md` is the preserved Phase 01 execution evidence.
`PUBLICATION_REVIEW.md` is the historical pre-publication review, not a claim
that the already-published baseline remains unpublished.

## Business rule authority

Customer-approved formulas are FINAL under [FIS-001](DECISIONS.md):

```text
Serviceability = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
Availability   = (FMC + PMCM + PMCS) / Total * 100
```

NMCM remains in the serviceability denominator. Existing zero-denominator guards
remain unchanged. `readiness.py`, existing readiness tests, and the synthetic
readiness fixture are protected baseline artifacts in Phase 01.6.

## Phase 01.6 scope

Engineering harness v1 supplies local unittest verification and tracked-file
security checks. Project instructions and README describe the workflow; this
document records state, `TASKS.md` records work, `RELEASE_GATES.md` records gates,
and `DECISIONS.md` remains the single decision register.

No dependency installation, SQL, operational data, ML model loads, FastAPI,
React, or packaging work is authorized in this phase. No automatic commit or
push is authorized. The harness reuses the laptop's existing Python environment.

## Execution evidence

Initial Windows PowerShell 5.1 verification command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe
```

Actual result: exit 0; **28 tests passed**, zero failures/errors/skips.
The inherited pandas date-inference warning remains unchanged. The first
security-script attempt exposed a PowerShell 5.1 parameter-default issue; it
was corrected before acceptance.

Final acceptance results (Windows PowerShell **5.1.26100.9818**):

| Actual command/check | Actual result |
|---|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe` | Exit 0; **11/11 harness checks passed**; explicit and automatic discovery each ran the unchanged 28 readiness tests successfully |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security_check.ps1` | Exit 0; 11 tracked files; 0 confirmed violations; 0 manual-review findings |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\AI\Projects\FIS4\scripts\security_check.ps1 -RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\proposed-security-review` | Exit 0; all **17 proposed files** scanned in an isolated index; 0 confirmed violations; 0 manual-review findings; fixture then removed |
| Protected-file comparison against baseline commit | Module, both existing Python test files, synthetic fixture, original report, runner, and decision register byte-identical |
| Legacy metadata before/after final harness regression | **18,034 files unchanged**; source hashes additionally checked by existing parity tests |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | Exit 0; no whitespace errors |
| Root index/HEAD | No staged changes; HEAD remains `a57936a8fff7e0502bceef008ea609fe4aef7379` |

The proposed-file scan used an explicit 17-file allowlist copied only from FIS4
into a disposable Git fixture. No legacy source was copied. No real working
repository files were staged; its tracked security scan intentionally does not
include the six new untracked files until approved staging.

Harness checks: explicit interpreter, automatic interpreter, invalid explicit
path (exit 2, no fallback), synthetic failing unittest (exit 1), zero tests
(exit 1), clean security fixture (exit 0), index review lead without value
disclosure (exit 0/REVIEW REQUIRED), working-tree review lead without value
disclosure, prohibited `.env` (exit 1), empty prohibited model-extension fixture
(exit 1, never loaded), and incomplete scan (exit 2). All passed. Synthetic
test repositories were removed after use. The earlier 10-check run also passed;
the final 11-check run added the explicit sensitive-file-type regression.

Phase 01.6 result: **PASS; awaiting commit approval**. No changes were committed
or pushed. No network/SQL/package-install operations were used in this phase.

## Git diff summary

Three existing files modified: `.gitignore` (ignore disposable harness fixtures),
`AGENTS.md` (end-of-task checks), and `README.md` (usage and limitations).
Their tracked diff is 71 inserted lines and no removals. Six new files are the
two scripts, `tests/test_engineering_harness.ps1`, and the three requested
state/backlog/gates documents. Untracked files are not included in `git diff
--stat` until staging. There are no readiness implementation/test/fixture changes.

## Known constraints

- The existing parity suite requires external, hash-pinned legacy source files
  at the documented laptop path. Those legacy files are not part of FIS4.
- Default system Python lacks pandas/NumPy; a compatible interpreter must be
  selected. No installation fallback is attempted.
- Security findings are heuristic, and manual findings require disposition.
  Untracked files need separate review and a post-staging scan before release.
- Sandbox command execution on this laptop has failed during process setup;
  verification uses authorized execution outside that failed sandbox. Git trust
  is scoped per command to the selected repository, not configured globally.
- Current verification is on this laptop, not an air-gapped destination. The
  Phase 00 destination/dependency/packaging uncertainties remain unresolved.
