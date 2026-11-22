# FIS4 release gates

## PR #7 mobile chart touch-scroll fix

- The new real browser touch-input regression reproduces zero movement before
  the CSS fix and verifies horizontal movement above 60 px in both themes after it.
- All 12 original history browser cases pass; the mobile regression adds one
  passing case and is intentionally skipped on desktop/tablet (13 pass, 2 skip).
- TypeScript, 61 component tests, production build and 139 backend regressions pass.
- Recovered harness result: exit 0, 12/12 checks including 134 passing portable
  tests; five external-reference tests excluded. No repeat needed for publication.
- Only the SVG touch-action value changes application behavior; readiness rules,
  backend, simulator, API contracts and dependencies remain unchanged.
- Physical mobile devices and iOS/WebKit remain unverified; no deployment acceptance.

## Phase 03B-2B Task 2 React historical dashboard acceptance

| Gate | Actual evidence / limit |
|---|---|
| Baseline / decisions | feature/phase03b2b-react-history at 726f343; FIS-001/FIS-002, backend/engine/simulator and original Python tests unchanged |
| Historical UI | API observations for 30/90/180/365 days; true date/0..100 axes, solid/dashed lines, hover/keyboard day detail and equivalent daily table; no readiness formulas or smoothing |
| Snapshot consistency | API-resolved date and selected command pinned across views; last historical point must match snapshot metrics/status counts; no stale/fabricated substitutes |
| Comparisons / composition | API command counts/metrics; compact six-status stack and matching labels; PMC aggregate retained while PMCM/PMCS remain separate |
| Provider/error boundary | CSV snapshots remain usable with explicit unsupported-history state; ordinary trend errors are isolated; SQL from health or later response clears metrics and blocks demo |
| Themes / accessibility | Light default, optional identical dark mode; native labelled controls, visible focus, chart keyboard/table equivalent; sampled text contrast >=4.5 and responsive overflow tests in both themes |
| Frontend verification | TypeScript and local Vite build PASS; Vitest 61/61 (original 32 retained); Playwright 27/27 (original 15 retained), actual fictional history backend, both-theme screenshots |
| Backend regression | Unchanged 139 full / 134 portable tests and 12/12 harness checks pass; external-reference exclusions explicit |
| Dependencies / network | No new packages/pins/lock changes; local SVG/CSS/system fonts/assets; normal and history demo configurations bind only loopback; no runtime CDN/external requests |
| Security / artifacts | Tracked scan exits 0, no violations; nine leads resolved (eight existing code expressions plus one benign Playwright-option documentation match); five new files scanned with no extra leads; screenshots/dist/caches ignored |
| Review / publication | Eighteen source/test/config/doc files remain unstaged/uncommitted; no commit, push, merge, deployment, SQL or ML work |

This accepts local fictional interaction and sampled browser accessibility,
not production security, full accessibility audit, customer design acceptance,
real SQL integration, FIS-002 offline release packaging or static FastAPI hosting.

## Phase 03B-2B Task 1 historical trend API local acceptance

| Gate | Actual evidence / boundary |
|---|---|
| Baseline / formulas | feature/phase03b2b-history-dashboard at 9ac0f9a; FIS-001/FIS-002, simulator and readiness engine unchanged |
| Additive contract | One GET history/series route, history mode only; existing endpoints/default provider/SQL implementation and original regression tests unchanged |
| Bounded windows | Required inclusive end in history, canonical 30/90/180/365 days, provider-allowlisted command, clipped start and actual point_count |
| Complete daily observations | Chronological cached metrics plus all six status counts; PMCM/PMCS separate; every-day fleet/command reconciliation and FIS-001 verified |
| Warm cache only | At most 365 dictionary lookups on one immutable cache reference; no generation, snapshot, event loading, pandas aggregation or growing query cache |
| Validation / failure | Unknown/duplicate/invalid keys rejected without echo; outside end 404; unavailable/incomplete cache 503 with no partial data |
| Payload | 1..365 observations; hard 262,144-byte uncompressed JSON cap checked after model validation/serialization; generic 500 on overflow, no truncation |
| Regression | 139 full / 134 portable tests pass, all original 120/115 retained; five external-reference exclusions unchanged; 19 new series tests |
| Harness / security | Original **12/12 harness scenarios pass** with extended counts; scanner exits 0, 0 violations, eight existing leads dispositioned; both new files explicitly scanned, no leads |
| Performance | All four windows x fleet/command x 30 warm TestClient requests measured; exact sizes/mean/median/range and transport limitations recorded in PROJECT_STATE |
| Scope / publication | Frontend unchanged; no packages, SQL, internet, ML, forecasts, packaging or deployment; all changes unstaged, no commit/push/merge |

This is local fictional-series acceptance, not production access-control/load/TLS
or FIS-002 offline release acceptance. Authentication remains absent. No synthetic
series access is registered for CSV or SQL modes, and incomplete history must
never produce a silently shortened successful period.

## Phase 03B-2A historical readiness API local acceptance

| Gate | Implemented / verified evidence |
|---|---|
| Baseline / decisions | feature/phase03b2-history-api at 37c8120; FIS-001/FIS-002 and original readiness implementation/tests unchanged |
| Simulator preservation | Existing generation algorithm/contracts and 19 simulator tests unchanged; no blocking defect required alteration |
| Explicit selection | Validated synthetic_history mode, required cutoff, fixed 160 tails/four commands/four years; default small CSV unchanged; SQL safeguards/settings isolated |
| API compatibility | New versioned history route only in explicit history mode; FleetResponse/source/error conventions reused; existing endpoint models and default/SQL semantics unchanged |
| Historical validation | Required real date, optional allowlisted command, unknown/duplicate keys rejected; inclusive coverage, 404 outside range, no fallback |
| Lifecycle / cache | Worker-thread lifespan initialization, lock and atomic publication, immutable bounded aggregates, defensive event copies, shutdown cleanup, safe sticky failure |
| Warm path | Dictionary reads only for historical and existing aggregates in history mode; patched generation/snapshot/metric functions prove no warm recomputation |
| Regression | 120 full / 115 portable tests passed, retaining original 98/93 and all FIS-001 regressions; five external-reference exclusions unchanged |
| Concurrency / isolation | Per-app initialization and HTTP concurrency tests, mutation protection, config/shutdown isolation; SQL/non-history route exposure rejected |
| Performance evidence | Cold 13.299 s; three dates x fleet/command x 30 warm requests measured; separate Python memory profile; limitations in PROJECT_STATE |
| Security / review | Tracked security scan exits 0 with eight existing resolved leads; all four new untracked files scanned with unchanged text rules, no additional leads; 12/12 harness checks pass |
| Scope / publication | No new runtime packages, external services, real SQL, simulator algorithm changes, React, ML/prediction or packaging; all work unstaged, no commit/push/merge/deploy |

Acceptance is local fictional API behavior, not authorization/access-control,
production load/TLS, actual SQL or FIS-002 offline release acceptance. Authentication
remains absent. Future deployment must enable lifespan and account for per-worker
cold generation/memory; no request-time fallback or global mutable cache is allowed.

## Phase 03B Task 1 simulator review boundary

| Gate | Evidence / disposition |
|---|---|
| Baseline | feature/phase03b-fleet-simulator starts at local main 25b1eaa5e8e464247d9b49e38c468d0aa03b9dd3 (merged PR #3); supplied extra SHA suffix documented in PROJECT_STATE |
| Population / coverage | Exactly 160 zero-padded fictional tails, four balanced commands, 1,461 complete days for default four-year example; all six statuses |
| Persistent history integrity | Episode/action timing, supply receipt before repair, non-overlap, legal persistent transitions, accumulated hours, inspection consumption/resets, depot lifecycles validated |
| Determinism / cutoff | Repeated full output frames/bytes identical; alternate seed valid/different; features_at uses observed end-of-day state without eventual outcomes |
| Regression | 98 full / 93 portable tests pass, retaining original 79/74; original 28 readiness regressions unchanged; five external-reference tests explicit |
| Harness | All twelve scenarios retained and pass, with count expectations extended for 19 simulator tests |
| Security | Tracked scan exits 0: no violations, eight existing resolved leads; six new files explicitly reviewed with unchanged text rules and no additional leads; no staging |
| Decisions / isolation | FIS-001/FIS-002, original readiness code/tests, API, React, fixture and Python pins unchanged; fictional assumptions only, no external access/new packages |
| Performance / integration | Full preparation measured, including independent snapshot cross-check; retained/peak memory limitations documented; future prepare-once/cache strategy only |
| Review / publication | Source and docs left unstaged; no commit/push/PR; further work requires its own authorization |

This accepts fictional generator integrity only. It does not validate physical
aircraft behavior, prediction usefulness, actual SQL integration, API/dashboard
integration, model training, cloud deployment or FIS-002 offline transfer. Future
integration must not regenerate four years of snapshots per dashboard request.

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

## FIS-002: Offline-first product and transfer acceptance

Authority: [DECISIONS.md, FIS-002](DECISIONS.md), recorded 2026-11-20
(Asia/Dubai). These are required future release/transfer gates, not claims of
current implementation or completed verification.

FIS4 must be fully developed, integrated and acceptance-tested before the
security-approved transfer to the air-gapped Windows intranet. Cloud demonstration
and intranet operation must use one product codebase, with cloud hosting treated
as deployment configuration. Passing mocked SQL tests or a synthetic demonstration
alone does not satisfy complete product/integration or offline release acceptance.

| Gate | Required evidence before transfer approval |
|---|---|
| Complete product integration | Development, integration and acceptance evidence covers the required product before transfer; no deferred destination-side source repair, training or dependency installation |
| Single product codebase | Cloud and intranet use the same FastAPI business logic, readiness calculations, rule-based prediction engine, ML inference code and API contracts; deployment configuration does not fork application logic |
| Self-contained release | One Windows x64 offline release ZIP includes compatible Python runtime, all dependencies/native libraries, compiled React assets and verified ML artifacts |
| Destination independence | Clean isolated Windows x64 validation succeeds without Node.js, npm, pip, internet access or model training on the intranet |
| Configuration-only deployment | Only approved SQL connection, approved local secret mechanism and required deployment settings are needed; no manual source-code changes or embedded credentials |
| Pre-connection verification | Bundled synthetic mode validates startup, API and UI before any authorized SQL connection |
| Deterministic operations | Start, stop, health-check, diagnostics and rollback scripts are supplied and their behavior is verified |
| Exact-package validation | Build and test the exact release package in a clean, network-isolated Windows x64 environment before transfer; evidence identifies the tested release and its ZIP hash |
| Integrity and inventory | Integrity manifests and dependency inventory cover the bundled runtime, dependencies, native libraries, compiled assets and verified ML artifacts |
| Security-approved transfer | A security-review package and verification evidence identify the exact release; findings are dispositioned and transfer is explicitly security-approved |
| External SQL dependencies | SQL schema/source contracts, permissions, TLS and operational dependencies that packaging cannot eliminate are documented, with acceptance evidence and any remaining blockers explicit |
| Business-rule preservation | FIS-001 customer-approved formulas, NMCM denominator contribution, zero guards and protected regression tests remain unchanged and pass |

Existing tracked-source security boundaries remain in force. Bundled runtimes,
libraries and verified model artifacts belong to a separately authorized release
assembly/review workflow; this decision does not authorize adding them to source
control or accessing models, credentials, operational data or databases now.

This documentation change grants no permission to install packages, alter
application behavior, build/deploy a release, commit or push. None of these new
release gates is marked complete by recording FIS-002.

## Phase 03A React dashboard final review gate

| Gate | Actual evidence / disposition |
|---|---|
| Architecture decisions | FIS-001 unchanged; FIS-002 commit 8bd2ba8 preserved; AGENTS/DECISIONS unchanged; offline single-codebase requirements remain binding |
| API-owned readiness | Frontend formats API values only; no readiness formulas or runtime aircraft fixtures; original backend/engine/tests unchanged |
| Synthetic-only demonstration | Actual API source shown; SQL health blocks aggregates; live synthetic FastAPI integration passes; no SQL Server testing |
| Local development | Vite and FastAPI bound to 127.0.0.1; fixed local proxy; no CORS/security changes or arbitrary API URL |
| Frontend checks | TypeScript PASS, Vite local compilation PASS, Vitest 32/32 passed |
| Browser acceptance | Playwright 15/15 across 1440x1000, 768x1024 and 1024x768; filters, source/errors, recovery, responsive layout, keyboard controls and sampled contrast verified |
| Asset/network boundary | Built HTML references local compiled JS/CSS; system fonts/inline SVG; browser tests assert no external page requests; no runtime CDN dependency |
| Backend regression | 79 full / 74 portable tests, 12 harness checks; zero failures/errors/skips; external legacy tests remain explicit |
| Dependency lock | 15 exact installed direct pins; lockfile v3, 169 resolved entries with public HTTPS registry URLs and integrity records; no dependency changes during review |
| Generated artifact exclusion | node_modules, dist, test-results, Playwright reports, Vite caches, workspace temp/cache and tsbuildinfo ignored; no generated files proposed |
| Security | Proposed and post-staging 44-file scans exit 0; zero violations; all 8 source-expression leads explicitly dispositioned in PROJECT_STATE |
| Design references | No approved reference available; validation pending; no visual matching claimed |
| Scope and publication | 23 reviewed Phase 03A files staged; generated artifacts excluded; FIS-002 commit preserved; no commit/push/merge or synthetic fleet simulator authorization |

This gate accepts the local synthetic dashboard, not a production or offline
release. FIS-002 exact-package isolated acceptance, real SQL integration, authentication,
cloud deployment, static FastAPI hosting and ML remain separate future gates.
