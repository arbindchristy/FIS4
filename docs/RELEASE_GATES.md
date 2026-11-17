# FIS4 release gates

These gates reuse `AGENTS.md`, the formula decision in `DECISIONS.md`, the
Phase 01 `TEST_REPORT.md`, and the historical `PUBLICATION_REVIEW.md`.
They do not create a second business-rule or approval authority.

| Gate | Required evidence |
|---|---|
| Formula integrity | FIS-001 unchanged; NMCM remains in the serviceability denominator; protected baseline diffs/hashes reviewed |
| Verification | `scripts/verify.ps1` exits 0, discovers all existing tests, and reports actual executable/count/results; skipped tests explicitly reviewed |
| Security | `scripts/security_check.ps1` completes; no confirmed violations; every manual finding disposition recorded |
| New files | Explicit human/source review before staging; rerun security after approved files become tracked |
| Data boundary | Only approved fictional fixture; no credentials, operational data, local configuration, models, environments, wheels, or logs |
| Legacy preservation | Legacy source hashes and tree metadata remain unchanged during relevant verification; no SQL or model execution |
| Review | Exact changes and Git diff checked; required docs/state/backlog updated; failures or incomplete checks reported |
| Publication | Explicit approval of reviewed content; inspect current remote history; agreed commit scope; normal push only; verify resulting remote/local SHA |

## Script exit codes

- Verification: 0 success; 1 failing tests or zero tests; 2 setup/runner error.
- Security: 0 no confirmed prohibited files (may still require manual review);
  1 confirmed violations; 2 incomplete inspection or empty tracked inventory.
- Manual-review-only security exit 0 is **not** publication clearance.
  Binary/large/missing-content findings mean content was not fully inspected.
- Security scans tracked index and working-tree files, not all Git history or
  arbitrary untracked files. Filenames/types are confirmed policy violations;
  secret patterns are review leads, with matched values suppressed.

## Phase 01.6 acceptance and publication boundary

Acceptance requires working scripts on the existing interpreter, all 28
readiness tests passing, meaningful failure/redaction checks, unchanged protected
baseline artifacts, and recorded actual results/diff. The current remote baseline
is `a57936a8fff7e0502bceef008ea609fe4aef7379`; Phase 01.6 changes are not part of
that published commit. Commit approval is a separate pending gate, and push
requires its own authorization in the active task.
