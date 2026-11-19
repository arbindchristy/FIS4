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
baseline artifacts, and recorded actual results/diff. Phase 01.6 publication is
recorded in locally verified `bb3abfd036c2c7c88a03abf7e9cee628dd638f1c`, matching
local HEAD, main and cached origin/main at the start of Phase 02A. No live remote
recheck occurred. This supersedes the old awaiting-publication status.

## Phase 02A acceptance boundary

| Acceptance requirement | Evidence |
|---|---|
| Synthetic source only | Fixed fictional fixture; no source-path/upload API; local aggregate GET endpoints |
| Formula integrity | Unchanged readiness.py and original 28 tests; API known answers and zero guards pass |
| Dedicated dependencies | FIS4 .venv, Python 3.13.7; 22 exact pins; pip check exits 0 |
| API contracts | 16 tests pass: schemas, known answers, reconciliation, validation, missing selections, safe internal errors |
| Full verification | 44 tests pass, zero failures/errors/skips; external requirements explicit |
| Portable verification | 39 tests pass, five external tests excluded; also passes with legacy loader blocked |
| Harness regression | Original 11 scenarios preserved; 12 total checks pass |
| Real HTTP | Five Uvicorn localhost routes pass; server stopped |
| Security and new files | 11 reviewed files staged by explicit authorization; post-staging scan covers 22 files with zero violations/manual findings; evidence in PROJECT_STATE |
| Scope and stop | SQL, ML, React, real data, offline packaging deferred; no commit or push without approval |

Acceptance covers local synthetic behavior. Production and offline deployment
are deferred. pandas date inference and the Starlette HTTPX adapter deprecation
are reviewed, non-blocking warnings documented in PROJECT_STATE.

Staged-review gate passed on 2026-11-18: 44 full tests, 39 portable tests and
12 harness checks passed, with no failures/errors/skips; security exited 0.
Protected files match the Phase 01 baseline. Commit and push remain separate
pending approval gates. No live remote or vulnerability-database query occurred.

## Phase 02B mocked-provider acceptance boundary

| Gate | Evidence / disposition |
|---|---|
| Formula integrity | readiness.py, original 28 readiness tests, 16 API tests, fixture and FIS-001 unchanged |
| Provider selection | Default synthetic; explicit validated SQL configuration and separate credentials; invalid modes fail; no discovery or fallback |
| SQL query safety | One allowlisted literal SELECT; bound TOP value; read-only intent; no free-form identifiers or queries |
| Resource bounds | Finite connection/query timeouts, bounded batches/rows, span and projected snapshot caps; overflow rejects whole load |
| Source contract | README documents required event history and unmapped fields; named maintenance view not assumed historical or queried |
| Mocked verification | 79 full / 74 portable tests pass, retaining original 44/39; 35 provider tests; 12 harness checks; no failures/errors/skips |
| Security | Proposed and actual post-staging scans cover 26 files; exit 0, zero violations; all 6 source-expression leads explicitly dispositioned in PROJECT_STATE |
| Dependency approval | User approved exact pymssql==2.3.3 installation; native import/signature and FreeTDS v1.4.26 verified; pip check passes; no connection opened |
| Localhost synthetic demonstration | User reported successful Phase 02B synthetic API demonstration on 2026-11-19; no actual SQL Server acceptance implied |
| Publication | 11 reviewed files staged and post-staging security checked; commit/push/merge remain pending explicit approval |

Passing mocks establishes adapter/API behavior only. It does not accept real SQL
Server 2019 integration, prove the source view exists or contains history, or
authorize actual database access. Real acceptance requires approved source mapping
and completeness, secret injection, SELECT-only permissions, TLS/certificate trust,
native driver/server behavior, consistent reads, concurrency, cancellation and load
evidence. The read-only connection hint cannot replace database authorization.

Phase 02B review gate passed on 2026-11-19: fresh 79 full / 74 portable tests,
12 harness checks and security scans exited 0. All tests have zero failures,
errors and skips. The successful localhost synthetic demonstration is recorded
as user-reported evidence; actual SQL Server testing remains unperformed.
Staging approval does not authorize committing, pushing or merging.
