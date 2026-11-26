# FIS4 release gates

## Phase 05B calibration gate v1.1

- Keep raw recovery primary and raw lr-c1 comparator. No sigmoid fit because
  all three forward folds failed the minimum time-block support.
- A locked horizon without adequate paired uncertainty cannot earn PASS.
  Require independently reviewed source, fixture tests and verified calibration
  seal before separately authorizing the one-time locked test. Phase 05C NO-GO.


## Phase 05B development-only acceptance - 2026-11-24

- Qualified isolated Windows runtime reused; no app dependency changes. Dataset/
  artifact hashes checked; no generation, baseline refit or untrusted model load.
- Training outcomes <=2023-11-20, development outcomes <=2024-11-20. Reserved
  statuses filtered before Observation construction; calibration/test outcomes,
  prevalence and performance NOT INSPECTED. No fit on development or later data.
- Fixed four-candidate plan, train-only missingness/encoding/scaling, all H=1..180,
  exact-date NMCS labels and identical published development cohorts required.
- Focused 14/14 isolated, 41/41 foundation, 28/28 readiness PASS; portable 229 run,
  221 passed/eight new isolated-only skips, all executed in isolated suite. Actual
  security, provenance, commands and interpretation recorded in PROJECT_STATE.md.
- Criteria fail: point-best LR C=1 is worse than recovery in mean Brier/log loss;
  no credible general ML superiority. Retain empirical baseline. Short-horizon
  hints or unsupported long-horizon intervals do not justify promotion.
- Frozen LR config is reproducibility evidence only. Calibration and locked test
  require separate authorization; Phase 05C remains NO-GO. No publication authorized
  for this update, no PR status change, merge, deployment or inference endpoint.
- FIS-001/FIS-002/FIS-003, readiness/API/simulator/frontend/SQL/Render and all
  production dependency pins remain unchanged. Actual operational and Linux/
  offline-package acceptance remain separate unverified gates.


## Phase 05B preparation / scientific-acceptance gate - 2026-11-24

- Partial preparation only: verified merged Phase 05A baseline; separate six-year
  fictional dataset, empirical baselines and development replay. Preserve the
  four-year dashboard world, formulas, APIs, simulator algorithm and app dependencies.
- Missing scientific dependencies block logistic/boosted ML candidates. No substitute
  performance, accuracy, calibrated-ML or training success may be claimed. Follow
  the explicit dependency fallback: no silent installs; no model artifact execution.
- Calibration and final chronological test remain reserved. Common validation
  references, purged target boundaries and train-only counts are required; tail/time
  overlap limits statistical independence. A marginal interval is not paired skill.
- Full Phase 05B scientific acceptance / Phase 05C: NO-GO until actual ML comparisons beat the
  strongest baseline with meaningful independent evidence, calibration and locked
  testing complete. Long-horizon baseline improvement here is negligible.
- Feature/source/provenance manifests and tests in NMCS_MODELING.md; actual focused,
  protected, portable/security evidence in PROJECT_STATE.md. New dependencies need
  separate modeling-environment/wheel approval; Windows/Linux compatibility and later
  offline-package/Render memory/cold-start/functional gates remain unverified.
- A preparation-only review PR may follow successful code/security checks without
  claiming full ML completion. No merge, deployment or dependency installation.


## PR #15 correction acceptance - 2026-11-24

- Labels, coverage and features must share as-of reference eligibility; a future
  global endpoint cannot enable a past fleet observation-gap reference. Validated
  target carry remains distinct from reference eligibility.
- Rolling-window NMCS starts use the preceding usable day without including its
  population in the window. Ongoing runs/unknown predecessors do not create starts.
- Pre-fix reproductions, final focused 41/41 and protected 28/28 PASS; final portable,
  staged security, corrected fictional counts and commands in PROJECT_STATE.md.
- Prior eligibility formula/counts are superseded by the corrected assessment;
  underlying four-year fleet coverage and 872 NMCS runs remain unchanged. No
  readiness, source/provider, simulator, dependency, model or deployment changes.
- Existing six-year, real-source, training authorization and customer runtime gates
  remain open; resolving these review defects authorizes no merge or deployment.


## Phase 05A exact-date NMCS foundation gate - 2026-11-24

- Applicable scope: NMCS occupancy at T+H, H=1..180, not any-onset, NMCM or combined
  NMC prediction. Current NMCS aircraft remain eligible. No model is trained/loaded.
- Require observed or explicitly validated reconstructed target status; missing
  target/cutoff coverage produces null, not a negative label. Carry approval and
  source/assignment/calendar assumptions must be resolved for real integration.
- Feature cutoff <= T; no future outcomes or latent simulator episode data.
  Explicit window coverage, null hours, episode censoring and leading-zero text IDs.
- Final 35 focused tests PASS; portable/security/protected results and actual
  commands in PROJECT_STATE.md. No readiness/API/simulator/frontend/deployment or
  canonical dependency changes; FIS-001/FIS-002/FIS-003 preserved byte-for-byte.
- Contract/feasibility: NMCS_FOUNDATION.md. Four years supports experiments, not the
  eventual six-year acceptance or validated operational performance. Overlapping
  examples are not independent failures. No accuracy/probability claim is allowed.
- Future Phase 05B requires separate training/dependency authorization, fictional
  dataset provenance, purged temporal evaluation and preprocessing fitted on train
  only. Later customer inference requires fresh Linux dependency/memory/cold-start/
  functional checks plus FIS-002 Windows offline exact-package acceptance.
- PR #14 is already merged in this baseline; prior deployment publication statuses
  below are historical. Neither that merge nor this foundation accepts Render
  hosting, real SQL, operational prediction or a separate NMCM implementation.


## Render Free-only focused preflight - 2026-11-23

Current publication status: [PR #14](https://github.com/arbindchristy/FIS4/pull/14)
is open on `feature/render-free-demo`; chief-architect source review approves the
deployment implementation. It is **not merged or deployed**. The approved approach
is Render Free at USD 0/month with Git-backed Docker; no paid compute or external
registry publication is required or authorized. Public-exposure approval, zero-charge
billing guards and actual Render build/startup/idle-wake acceptance remain open.
The verification and no-publication statements below describe their historical
preflight execution points, not the current PR status.

Customer decision: Render Free USD 0/month only; supersedes the earlier paid-candidate
recommendation below. Existing image reused; one 0.1 CPU/512 MiB startup, no rebuild.
Probe exit 0: readiness 557.6507 s; peak 263.42 MiB, warm 212.44 MiB; zero OOM.
20 sequential API, four concurrent requests and five subsequent health checks pass.
Focused portable deployment-test TypeScript exit 0; two browser cases pass in 6.3 s.
Original Docker/runtime/lock/POC spec unchanged; no application or dependency changes.
CONDITIONAL GO for pre-warmed fictional demo only. Actual Render build/idle wake,
unauthenticated public exposure approval and USD 0 billing guards remain open.
Git-backed Docker needs no external registry; exact ten-file PR allowlist, commands,
limits, security dispositions, smoke/rollback steps: deploy/demo/PREFLIGHT_REPORT.md.
No stage/commit/push/PR/deployment/account or billing operation performed.
Final security exit 0: 71 tracked/index files, zero violations; ten existing benign
leads dispositioned in report. Eight untracked files: zero extra leads. Whitespace,
protected scope, empty index and five original deployment file hashes PASS.


## Future 180-day separate NMCS/NMCM ML release gate

Integrating 180-day separate NMCS and NMCM ML prediction requires a fresh Linux
dependency, memory, cold-start and functional acceptance assessment before
customer release. The current synthetic-readiness preflight does not establish
compatibility or capacity for that future integration and authorizes no ML work.

## Historical synthetic Docker/Render demo preflight gate (superseded)

The paid-compute/Starter, registry-digest and pending-portable-test requirements
below are retained only as historical decisions. The approved Render Free /
Git-backed Docker approach supersedes them; portable tests and PR publication are
complete. Existing measurements remain evidence. Current open gates are listed
above; CVE and Windows offline acceptance remain separate requirements.

- Existing main-based image/build evidence accepted without repeating the build.
  Fixed synthetic launcher, original business APIs/formulas, compiled local assets,
  one worker and no SQL/models/customer data; no HTTP source/debug/docs exposure.
- 0.5 CPU/512 MiB local profile measured: 94.12 s readiness, 276.64 MiB peak,
  217.77 MiB warm; nine focused constrained-browser cases pass. Details and exact
  commands in deploy/demo/PREFLIGHT_REPORT.md; not Render performance evidence.
- CONDITIONAL GO: access/origin controls and paid compute require explicit approval.
  No authentication is implemented. Minimum local demo candidate Starter; no free
  tier reliability claim. Actual Render configuration/rollback remains untested.
- Portable PR test adaptation, final staged security, vulnerability/supply-chain
  review and approved immutable registry digest remain future publication gates.
- Preserve FIS-001/FIS-002/FIS-003 and the separate Windows offline-package gates.
  No public deployment, registry push, purchase, commit or PR performed.

## P0 selected-command reporting gate

- This correction supersedes the earlier fleet-always presentation rule. All Commands
  shows the fleet; a selected command controls all primary KPIs, counts, distribution
  and historical trend. Scope headings/labels must agree with the rendered snapshot.
- Distinct fleet/A/B fixtures and a negative pre-fix run are required, alongside
  actual HTTP/browser All -> A -> B -> All evidence. Passing counts alone do not
  establish scope acceptance. Requirement-to-test mapping is in PROJECT_STATE.
- Keep nested platforms command-owned, API percentages unchanged, and date/windows,
  abort/stale/source/error guards intact. Failed command data must never substitute
  fleet metrics or history. All Commands retains date; reset returns latest fleet.
- TypeScript/build pass; 136 regression tests and eight final scope tests pass;
  browser 47 pass/four intentional skips, plus three final scope demos pass. Security
  exit 0, zero confirmed violations, 10 existing benign leads dispositioned.
  Exact commands, HTTP evidence and requirement-to-test matrix are in PROJECT_STATE.
- Protected backend, simulator, decisions, dependencies and historical engine remain
  unchanged. Physical-device/iOS, actual SQL/authentication/offline acceptance remain
  deferred. No staging/publication; chief-architect source review required.

## Command-centric readiness review gate

- Exactly one primary summary per command; command-owned expandable platforms,
  no competing flat platform interface, no battalion exposure.
- Overall fleet overview remains above filtered commands. API-owned percentages;
  count reconciliation at fleet/command/platform levels; NMC count is NMCS + NMCM.
- Existing contracts and history engine preserved; lazy loading, cancellation,
  stale-response protection, source isolation, keyboard/touch/themes retained.
- TypeScript/build pass; 128 frontend tests pass; strengthened six command tests
  pass. Browser: 44 pass/four intentional skips, zero retries; both touch tests pass.
- Security: exit 0, zero confirmed violations, 10 existing leads dispositioned;
  new untracked command test explicitly scanned with no additional leads.
  Exact commands, startup failures and final evidence are in PROJECT_STATE.
- Backend, simulator, provider, formulas, decisions and dependencies unchanged;
  backend/portable/harness suites intentionally not repeated for frontend-only work.
- Physical device/iOS/WebKit, full accessibility, actual SQL, authentication,
  prediction and offline-release acceptance remain deferred. Chief-architect source
  review required; nothing staged, committed, published or deployed.

## Phase 03C-1B.2 frontend verification review gate

- TypeScript, 122/122 unit tests and production build pass, exit 0.
- Full Edge browser suite: 41 pass/four intentional non-mobile touch skips,
  45 total, no retries; strengthened preservation follow-up six/six pass.
- Actual synthetic contracts, six-status count reconciliation, combined filters,
  all windows, safe errors/source blocking and cancellation/stale protection tested.
- Both overview percentages and command cards remain API-owned and unchanged by
  platform selection. No readiness formulas or fallback observations in React.
- Desktop/tablet/mobile, light/dark, keyboard inspection and actual CDP mobile touch
  pass; six final platform screenshots visually reviewed and retained locally.
- Security exit 0: zero confirmed violations, 10 existing leads dispositioned;
  explicit four-new-file review adds zero leads. Scanner rules unchanged.
- Only frontend/tests and three records changed; backend, simulator, decisions,
  protected baseline and dependencies unchanged. No Python/harness suites repeated.
- Physical devices/iOS/WebKit, full accessibility audit, actual SQL, prediction,
  authentication and offline package acceptance remain deferred.
- Await chief-architect review; no staging, publication or deployment.

## Phase 03C-1B.1 frontend implementation gate

- Platform clients/section written using existing React/Vite and design system;
  comparisons reconcile counts to the effective snapshot; independent platform
  drilldown and shared windows; no client-side readiness formulas.
- Existing chart reused with platform context; cancellation/key guards and safe
  contained error states implemented. Product identity updated; fictional/no-auth
  warnings preserved. Runtime correctness remains to be verified.
- Focused TypeScript check passed (exit 0), after correcting two new narrowing
  errors. No dependency, backend, simulator, SQL or prediction changes.
- Unit/browser/build and all Python suites were deliberately not run under the
  user's implementation-only instruction. Previous backend evidence is historical.
- Phase 03C-1B.2 must add/adapt frontend fixtures/tests, exercise reconciliation,
  source isolation, malformed/stale responses, all windows, both themes and mobile
  touch/keyboard behavior, then run frontend gates and applicable security checks.
- Await chief-architect source review; no staging, publication or deployment.

## Phase 03C-1A platform backend review gate

- Synthetic-only platform metadata; stable tail/platform/current-command identity;
  original population/status trajectories and FIS-001 metrics preserved.
- Additive history-only list/comparison/trend routes with combined filters; existing
  unfiltered routes, CSV/SQL isolation and React unchanged.
- All six statuses, every-day command/platform reconciliation, bounded windows,
  strict safe errors, immutable concurrent warm-cache reads and no hierarchy leakage.
- Fictional intra-day/missing-day parity fixtures use the unchanged Streamlit-style
  readiness engine; Enhanced1 reconstruction is not substituted.
- 21 focused, 160 full and 155 portable tests pass; five external-reference
  exclusions explicit. All 12 harness checks pass; unchanged scanner exits 0,
  zero confirmed violations and 10 existing leads dispositioned. The new untracked
  test is explicitly scanned/reviewed with no extra leads. Actual commands/evidence
  are in PROJECT_STATE.md; chief-architect review remains required.
- No live SQL, prediction, physical integration, authentication or offline release
  acceptance is claimed. No new dependencies or publication actions.

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
