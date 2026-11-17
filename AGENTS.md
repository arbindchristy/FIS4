# FIS v4 project instructions

## Customer-approved readiness formula lock

The user explicitly confirmed the original Streamlit v3.10.4 executable
readiness formulas as FINAL. See [docs/DECISIONS.md](docs/DECISIONS.md), decision
FIS-001. Apply these rules to every fleet and command calculation:

```text
SERVICEABILITY (%) = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
AVAILABILITY (%)   = (FMC + PMCM + PMCS) / Total * 100
```

NMCM MUST remain in the serviceability denominator. Do not subtract NMCM.
Do not change these business formulas, status contributions, or regression
expectations without a new explicit customer-authorized instruction that
supersedes FIS-001. Legacy comments suggesting NMCM exclusion are incorrect
documentation and must not override the approved executable behavior.
Do not treat the documentation discrepancy as an unresolved formula decision.

Preserve the existing zero-denominator guards. Fleet and command metrics must
use the same formulas. Run the existing 28 Phase 01 tests after relevant work;
do not weaken tests to permit a formula change.

## Project boundaries

- Legacy reference `C:\AI\Projects\fleet_cpi_suite` is read-only.
- Keep new work inside `C:\AI\Projects\FIS4`.
- Do not access credentials, SQL, operational fleet data, or joblib models
  without a separate explicit instruction authorizing that scope.
- Do not install packages or begin FastAPI, React, or packaging work without
  a separate instruction.

## End-of-task engineering checks

Run `scripts/verify.ps1` and `scripts/security_check.ps1` at the end of future
tasks. Use `-PythonExecutable` when interpreter selection must be explicit.
Record the actual commands, exit codes, test count/results, and any unresolved
manual security findings in the task report. A nonzero check exit code blocks
completion; manual-review findings require disposition before publication.
The security check covers tracked index and working-tree content; untracked
files require explicit review before staging, followed by another security check.

Keep `docs/PROJECT_STATE.md`, `docs/TASKS.md`, and `docs/RELEASE_GATES.md` current.
Reuse `docs/DECISIONS.md` for decisions and `TEST_REPORT.md` for Phase 01 evidence;
do not create competing governance files or rewrite historical test evidence.
Do not commit or push without the approval required by the active task.
