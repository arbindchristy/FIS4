# FIS4 helicopter readiness dashboard

## Phase 03B-2B Task 2: React historical helicopter dashboard

The existing dashboard now includes 30/90/180/365-day API trends, synchronized
date/command selection, command counts, six-status composition, keyboard/hover
inspection and an accessible daily table. Light is the default; the theme toggle
provides the same data in dark mode. No chart/theme package was added. The UI
identifies all data as fictional historical helicopter data, not live intelligence.
CSV snapshots still work with an explicit history-not-enabled message; SQL remains
blocked. All readiness percentages originate from the backend.

For a local historical demonstration, use two terminals from FIS4:

```powershell
# Terminal 1: fixed fictional history, loopback 8001 (test/demo helper only).
.\.venv\Scripts\python.exe -B frontend\e2e\history_backend.py
# Terminal 2:
cd frontend
npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run dev -- --mode history-demo
```

Open `http://127.0.0.1:5174`. Vite's explicit history-demo mode proxies only to
127.0.0.1:8001. Normal development still uses 5173 -> 8000 and the default CSV API.
No credentials, external hosts or provider selectors are accepted from the browser.
The helper is not an offline release/start-stop solution. FIS-002 packaging and
future FastAPI static serving remain separate work; production assets compile
locally without runtime CDN dependencies.

Actual commands/results, screenshot paths, security dispositions and limitations
are in docs/PROJECT_STATE.md. Both plot and daily table can scroll within their
panels on narrow screens, without page overflow. Theme choice is session-local.

## Phase 03B Task 1: offline fictional fleet simulator

Phase 03B-2A adds an explicitly selected history provider and
`GET /api/v1/readiness/history?date=YYYY-MM-DD&command=FICTIONAL_A` (command optional).
See [historical API configuration and contract](docs/HISTORY_API.md). The default
API still uses the small CSV fixture; history generation/aggregate preparation
runs once at lifespan startup only when selected. No authentication is implemented.

`simulator/` generates reproducible event/history tables and validated daily
snapshots for 160 fictional tails across four commands and four calendar years.
It is separate from the API/dashboard and uses the unchanged readiness engine.
No new packages, SQL, real records, prediction or ML are required.

```powershell
.\.venv\Scripts\python.exe -B -m simulator --as-of 2026-11-20
```

See [the simulator schema and generation guide](docs/SIMULATOR.md) for configuration,
optional ignored CSV exports, prediction-date boundaries and the proposed cached
FastAPI integration. Actual verification evidence is in docs/PROJECT_STATE.md.

## Phase 03A local dashboard

`frontend/` contains the React/TypeScript/Vite dashboard. All readiness metrics,
aircraft counts and status percentages come from the existing FastAPI endpoints.
The frontend formats percentages to one decimal place; it implements no readiness
formula and contains no runtime aircraft fixtures. Fictional response fixtures
exist only in frontend tests and are not imported by application modules.

The dashboard presents fleet Serviceability/Availability, Total Tails/FMC/PMC/
NMCS/NMCM/DEPOT counts, command comparisons and all six canonical statuses.
It provides date and command filters, latest-snapshot reset, retry, loading,
empty-data, invalid-filter, source-mismatch and API-error states. Selected source
is reported from the API rather than assumed. A SQL health response is labelled
SQL and blocks all aggregate requests: this demonstration accepts synthetic mode
only. Health checks are liveness-only and never establish SQL integration acceptance.

Data flow: health source check, unfiltered command report to resolve the requested
or latest API date and available commands, then parallel aggregate requests pinned
to that exact date. Date/command/source mismatches, invalid metrics, missing statuses
and malformed payloads fail closed. Changing filters clears old metrics; cancelled
or stale responses cannot replace current data. API error details are not echoed.
The dashboard never starts a SQL connection or supplies provider credentials.

No approved dashboard design reference was found in the FIS4 workspace. The navy,
teal and neutral layout is a new implementation, not a claimed visual match.
Design-reference validation remains pending. Desktop/tablet layouts use local
CSS, native form controls, labelled meters, visible focus and skip navigation.
Fonts are installed system fonts; no external images, scripts or fonts are loaded.

### Local development

Validated tool versions and actual results are recorded in PROJECT_STATE.
Frontend dependency installation requires explicit approval. From the repository
root, start the existing synthetic backend (no SQL configuration or secret input):

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In another terminal, enter `frontend/`. After approved dependency installation,
the normal reproducible install is `npm.cmd ci --ignore-scripts --no-audit --no-fund`.
Then run:

```powershell
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Vite binds only to 127.0.0.1 with strict port 5173;
it proxies `/health` and `/api` to `http://127.0.0.1:8000`. Requests are same-origin,
so no backend CORS or security setting change is required. There is no arbitrary
API URL, SQL mode selector or credential configuration in the application.
Application code reads no `VITE_*` variables or configuration files; Vite's
standard build-time environment handling is not used for API/secret settings.
Keep both servers on localhost; do not use `--host 0.0.0.0`.
Authentication is not implemented; local synthetic demonstration is the scope.

Use dates returned by the API. The existing fictional fixture spans
2026-01-01 through 2026-01-03; an empty date asks the API for its latest snapshot.
The command menu is derived from that date's unfiltered API command report.
Dates/commands outside available data produce an empty state rather than fabricated
counts. The frontend does not claim the selected snapshot is wall-clock current.

### Frontend checks and future asset serving

From `frontend/`:

```powershell
npm.cmd run check
npm.cmd test
npm.cmd run build
npm.cmd run test:e2e
```

Vitest/Testing Library tests cover components and the HTTP client through mocked
responses. Playwright tests start owned localhost FastAPI/Vite servers and use
the preinstalled Microsoft Edge browser at 1440x1000, 768x1024 and 1024x768.
No browser download is needed. Ports 8000 and 5173 must be free before these tests;
they intentionally refuse to reuse an unknown running server. SQL health/error
responses used by browser tests are intercepted fictional responses, not a SQL
backend. Test screenshots/reports are generated under ignored verification paths.

`npm run build` checks TypeScript and compiles a local bundle into ignored
`frontend/dist/`; this is compilation verification only. It is not a production
deployment or offline package. All application assets are bundled locally and
API paths remain relative. A future separately authorized phase can serve these
static files and an SPA fallback from FastAPI, preserving `/api` and `/health`.
Node.js is a development/build tool; the intended intranet runtime will serve
compiled assets and will not require Node.js. No backend static mount, production
packaging, React Phase 03B work, actual SQL integration or ML work is included here.

The existing Python verification and PowerShell harness commands below remain
unchanged; frontend test results are recorded separately from the 79 full / 74
portable backend tests and 12 harness checks. Run the security scanner, explicitly
review new source/lock files, then rescan after separately approved staging.

## Historical Phase 02B implementation

## Phase 02B providers (mocked SQL acceptance only)

The current branch adds an explicit event-provider boundary. The default app
remains synthetic: `python -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000`.
It does not discover environment variables, local configuration files, credentials
or databases. No live SQL connection/query is authorized by this phase.

`api/providers.py` defines `DataProvider.source` and `load_events()`. Both modes
feed the unchanged `coalesce_columns` and `build_tail_daily_snapshot` functions
before the readiness metrics. The synthetic provider retains the same fixed CSV,
text-tail loading and invalid-date behavior. The SQL provider validates records
strictly before normalization; invalid SQL data fails the entire request rather
than silently dropping records or repairing numeric tail identifiers.

### Explicit configuration and secrets

`parse_config(mapping)` validates mode and settings, defaults to synthetic, rejects
unknown fields/modes/identifiers, and emits a generic configuration error without
raw inputs. A nonsecret SQL template is in `config/sql-provider.example.json`;
its host uses the reserved `.invalid` domain and is never loaded automatically.
Credentials are intentionally absent. An authorized deployment composition root
would explicitly pass `SqlCredentials` from its approved secret mechanism:

```python
from api.config import parse_config
from api.main import create_app

# config_values: explicitly supplied nonsecret configuration mapping.
# approved_credentials: SqlCredentials supplied outside source control.
# With no arguments create_app() stays synthetic; configuration alone is not a connection.
app = create_app(parse_config(config_values), credentials=approved_credentials)
```

No secret mechanism is accessed or implemented in this phase. Do not put real
credentials into the template, source, command line, Git, logs or responses.
`SqlCredentials` hides username/password representations and JSON serialization.
Do not log secret objects' raw values, arbitrary config input or driver exceptions.
SQL mode without credentials fails construction. Provider/connector injection
supports mocks through `create_app(..., connection_factory=mock)` or FastAPI's
`get_provider` dependency override; neither requires a real server.

### Required SQL source contract and unmapped fields

No schema, data types or history were inspected on
`mod.VW_MNT_AIRCRAFT_SERVICEABILITY`. Its history semantics are **unknown**. It is
not allowlisted or queried. A reviewed adapter/view meeting the following contract
is required before real integration can be accepted. The proposed
`[fis].[readiness_events_v1]` name is a contract target, not an existing-object claim.

| Required column | Required source semantics |
|---|---|
| `event_time` | Non-null SQL datetime2, returned as a timezone-naive Python datetime; agreed calendar timezone; pandas-compatible range |
| `tail` | Non-null textual unique aircraft identity, at most 64 printable characters; retain leading zeros at the database source |
| `status` | Nonblank printable text, at most 64 characters, mapped through existing readiness aliases; unknown values remain unknown and in totals |
| `command` | Nonblank text, uppercase letters/digits/underscore/hyphen, at most 32 characters; command at event time, including transfers |

The SELECT aliases event_time to `date`. Column mapping, keys, timestamp/timezone,
status-code meanings, command ownership/transfer history, retention, deletions,
and complete initial/carry-in state are all **unverified/unmapped** against the
named maintenance view. Optional platform, location, reason, hrs_to_insp and
hrs_to_phase are intentionally not mapped or queried. A numeric tail cast to text
cannot recover lost leading zeros and is not an accepted source remedy.

The approved snapshot engine forward-fills each tail from its first event through
the global last event date, with no earlier backfill. Therefore the SQL source
must supply a complete, coherent event set for the intended analysis window,
including each tail's required initial state and historical commands. A current
status-only view cannot establish historical readiness. The adapter cannot prove
upstream completeness. API date/command selection happens **after** loading and
snapshot construction; request filters never truncate history before forward-fill.

Exact normalized retransmissions are deduplicated by the SQL adapter. Conflicting
records with the same timestamp/tail are rejected: there is no approved business
tie-break rule. This does not alter the readiness engine or synthetic semantics.

### Query, limits, connection lifecycle and errors

The only selectable source key is `readiness_events_v1`, selecting a complete,
literal SELECT with explicit allowlisted identifiers. There is no free-form SQL,
identifier interpolation, procedure execution or DML. `TOP (%s)` binds the
validated row limit plus one as a value parameter; no API value enters SQL text.
No date/command WHERE clause is pushed down, preserving snapshot inputs.

Default limits: login 5 seconds (1–60), query 15 seconds (1–120), 10,000 events
(maximum 100,000), fetch batches of 500 (maximum 1,000), 366 calendar days per tail
(maximum 3,660), and 100,000 projected snapshot rows (maximum 1,000,000). One excess
event rejects the entire load. No partial/truncated metric result is returned.
Bounded fetchmany replaces fetchall; span and projected snapshot size are checked
before expansion. Limit selection and full-history sizing require later acceptance.

Each load owns and closes its cursor/connection on success or failure, with no
commit. Connections request UTF-8, TDS 7.4, datetime2, required encryption and
read-only intent. Read-only intent is not an authorization boundary: a separately
provisioned SELECT-only principal on the approved source is still required.
Encryption, certificate/hostname trust, permissions, SQL Server 2019 behavior and
FreeTDS configuration remain real-integration gates, not mocked claims.

FreeTDS login/query timeout settings are process-wide; this application serializes
SQL loads with a bounded lock wait. Other code using pymssql in the same process
must not bypass this policy. Driver timeouts are not an end-to-end request deadline
or a bounded server-side query plan. Concurrency/load and cancellation require
separate real-server acceptance. See the [official pymssql reference](https://pymssql.readthedocs.io/en/stable/ref/pymssql.html).

Routes and existing synthetic response bodies are preserved. All responses gain
`X-FIS4-Data-Source`. Successful SQL responses and health use `source: sql`;
health remains liveness only and does not connect. SQL-provider failures return
503 with `{"detail":"SQL data unavailable","source":"sql"}`. SQL 404/422/500
errors also report `source: sql`; no failure returns synthetic data. No automatic
retry or fallback is implemented. Internal driver exception text is neither logged
nor exposed. OpenAPI adds the SQL source value, optional error source and 503.

### Dependencies and test boundary

The sole added dependency is `pymssql==2.3.3`; all 22 Phase 02A pins remain unchanged.
[The pinned release](https://pypi.org/project/pymssql/2.3.3/) publishes a CPython 3.13
Windows x64 wheel. Installation requires explicit user approval. The provider
imports the driver lazily and enforces version 2.3.3; mock and synthetic tests do
not require a native driver or a connection. Driver import/package validation,
if approved, establishes laptop compatibility only, not SQL integration.

Current full suite: **79 tests = original 44 + 35 provider tests**. Portable:
**74 = original 39 + 35**. The five external legacy-reference tests are unchanged.
Harness regression retains **12 checks** (including the original 11 scenarios),
with updated full/portable inventory expectations. Use the Phase 02A verification
commands below; `verify.ps1` already discovers the new tests. `test_providers.py`
uses only generated fictional credentials and injected DB-API mocks; no live SQL
test is included. Tests cover bounded retrieval, strict configuration, safe
cleanup/errors, source reporting/no fallback, ordering, duplicate events, tail
text, snapshots, and fleet/command/status reconciliation. Actual execution and
security findings are recorded in PROJECT_STATE.

Mocked acceptance does not authorize connecting to a database, reading real fleet
data, deploying SQL mode, installing dependencies, or publishing changes. Those
actions need their own explicit authorization. React, ML and packaging stay deferred.

## Historical Phase 02A implementation

Phase 02A adds a local, read-only FastAPI backend using only the approved
fictional fixture. SQL, ML, React, operational data, and offline packaging remain
out of scope. `readiness.py` and FIS-001 are unchanged. Phase 01.6 was published
as `bb3abfd036c2c7c88a03abf7e9cee628dd638f1c`; see the locally verified
publication correction and current acceptance evidence in [project state](docs/PROJECT_STATE.md).

## Phase 02A setup and use

Validated on Windows, CPython 3.13.7 x64. Create a dedicated environment from
the repository root; no legacy environment is used or modified:

```powershell
C:\Python313\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

The exact runtime and test dependency closure is pinned in `requirements.txt`.
FastAPI/Starlette/Pydantic provide routing, validation and schemas; Uvicorn
provides ASGI serving; HTTPX/httpcore provide in-process contract testing;
pandas/NumPy provide the protected calculation baseline. Other pins are their
resolved dependencies (including FastAPI's OpenTelemetry API dependency; no
exporter is configured). pip 25.2 bootstraps this environment and is not an app
dependency. These pins establish the tested Windows environment, not an offline
bundle or a guarantee for other Python/platform versions.

| GET endpoint | Response |
|---|---|
| `/health` | Liveness only: `status: ok`, `source: synthetic`; does not read data |
| `/api/v1/readiness/fleet` | Selected day's fleet metrics |
| `/api/v1/readiness/commands` | Selected day's command metrics, sorted by command |
| `/api/v1/status-distribution` | Counts and percentages for all six canonical statuses, including zeros |

Aggregate routes accept optional `date=YYYY-MM-DD` and `command=A` query
parameters. Date defaults to the latest fixture snapshot, **2026-01-03**, rather
than wall-clock today. Commands are case-sensitive, 1–32 uppercase letters,
digits, underscores or hyphens. Unknown query parameters, invalid dates and
invalid command syntax return 422; absent dates/commands or empty snapshots
return 404. Internal failures return a generic 500 without exception details.
Errors use `{"detail": "..."}`. OpenAPI is at `/openapi.json`, interactive
documentation at `/docs` (its browser assets use a CDN; offline docs are deferred).

All aggregate responses include `source: synthetic`, selected `date` and nullable
`command`. Fleet responses nest `metrics`; command responses contain `commands`.
Counts use baseline names (`total_tails`, `fmc_tails`, `pmc_tails`, `nmcm_tails`,
`nmcs_tails`, `depot_tails`); percentages use `svc_pct` and `avail_pct`, with full
float precision. Distribution separates PMCM and PMCS; each status has `status`,
`count`, `pct`, with unknown statuses appended if present. No raw tail records,
uploads, arbitrary source paths, authentication, or write endpoints are provided.
This acceptance gate covers local synthetic use; production deployment is deferred.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security_check.ps1
```

Full mode runs the original **28 readiness tests plus 16 API tests**. Portable
mode runs **23 readiness plus 16 API tests**, excluding five explicitly named
external-reference tests via `tests/suite_selection.py`. These are all four
`LegacyParityTests` methods and
`MetricTests.test_true_null_commands_do_not_reconcile_and_match_legacy`.
Portable mode never loads legacy source files; exclusions are reported separately
from skips. Full mode requires the existing hash-pinned external references and
fails if they are unavailable or changed. Direct unittest discovery remains full
mode. Harness regression preserves its 11 original scenarios and adds portable
selection for **12 checks** total.

Automatic interpreter selection now checks `FIS4_PYTHON`, project `.venv`, project
`venv`, then PATH. Candidates must import the API/test dependencies as well as
pandas and NumPy. The sibling legacy environment fallback has been removed.
The earlier instructions below describe historical Phase 01/01.6 behavior;
use the Phase 02A commands above for current verification. Do not run the report
generator to replace the preserved Phase 01 `TEST_REPORT.md`.

Known warnings: the inherited pandas date-inference warning is retained to
preserve baseline parsing. Starlette 1.10.0 deprecates its HTTPX test adapter;
HTTPX 0.28.1 remains functional in all 16 contract tests. Migration to the new
adapter is deferred; no warnings are suppressed.

## Historical Phase 01 baseline

This phase isolates readiness calculations before any API, UI, ML, or release work.
All data in `data/synthetic_readiness.csv` is newly authored fictional test data.
The module performs no file, network, SQL, Streamlit, or model operations.

The readiness formulas are **CUSTOMER-APPROVED / FINAL**, based on explicit
user confirmation on 2026-11-17. NMCM remains in the serviceability denominator.
See [decision FIS-001](docs/DECISIONS.md) and [project instructions](AGENTS.md).
Unauthorized formula changes are prohibited.

## Engineering harness (Phase 01.6)

From the repository root, run the following in PowerShell. Use the explicit
interpreter form when automatic selection is inappropriate:

```powershell
& .\scripts\verify.ps1
& .\scripts\verify.ps1 -PythonExecutable 'C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe'
& .\scripts\security_check.ps1
```

If the local policy blocks unsigned scripts, an allowed process-scoped invocation
is `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
(subject to organizational policy). It does not change machine execution policy.
Both scripts run locally without installation or network access.

`verify.ps1` tries `FIS4_PYTHON`, project `.venv`, project `venv`, the audited
sibling legacy virtual environment, and `python.exe` on PATH, in that order.
Each candidate must import unittest, pandas, and NumPy. An explicit executable
never silently falls back. All `test*.py` unittest tests are discovered from
`tests`, and bytecode writes are disabled. The script reports the actual Python,
test count, failures, errors, skips, and result without rewriting `TEST_REPORT.md`.
Exit codes: 0 = tests pass; 1 = failed tests or zero tests; 2 = setup/runner error.
Skipped tests are reported and require release review; they are not automatically
test failures. Existing legacy parity tests still require the documented local
read-only references and their pinned hashes.

`security_check.ps1` inventories Git-tracked index entries and checks both index
content and current tracked working files. Confirmed prohibited paths/types,
unmerged entries, and links/submodules fail with exit 1. Obvious credential/token
patterns, private network/endpoint patterns, oversized files (over 1 MiB), binary
content, and missing working files are manual-review findings; only locations
and rule names are printed. Manual-review-only scans return 0 with **REVIEW
REQUIRED**, not a clean PASS. Exit 2 means incomplete inspection or an empty
index. A scan cannot establish that data is synthetic or a token is live;
human review and the release gates remain necessary.

Untracked files are intentionally outside the normal security scan. Review them
explicitly before staging, then rerun the scan after approved staging. Pattern
scans are not a full secret detector and do not inspect history or prove the
absence of operational information. Existing approved local reference paths
remain documented in the historical publication review.

Harness regression checks (separate from the unchanged 28 readiness tests):

```powershell
& .\tests\test_engineering_harness.ps1 -PythonExecutable 'C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe'
```

These checks create a disposable Git fixture under ignored `.harness-test-tmp`,
exercise synthetic failure/security cases, and remove the fixture afterward.
Read [project state](docs/PROJECT_STATE.md), [task backlog](docs/TASKS.md), and
[release gates](docs/RELEASE_GATES.md) for current status. Formula authority
continues to be [FIS-001](docs/DECISIONS.md); the harness does not change formulas.

## Run the verification

From PowerShell in `C:\AI\Projects\FIS4`:

```powershell
& C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe -B run_phase01.py
```

This uses the already installed CPython 3.13.7 x64, pandas 2.3.3, and NumPy 2.3.4.
No dependency installation is required. The default `C:\Python313\python.exe`
does not have pandas installed. `-B` prevents Python bytecode writes.
The runner writes `TEST_REPORT.md` only in FIS4 and exits nonzero on failure.
It compares metadata of all legacy files and SHA-256 hashes of reviewed sources
before/after verification. It reads legacy source, but no legacy CSVs,
configuration contents, credentials, or model files. Tree checks read metadata only.

For ordinary unittest output without generating the report:

```powershell
& C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

The second command is provided for reproduction; consult `TEST_REPORT.md` for
the command actually executed for acceptance.

## Deliverables

- `readiness.py`: standalone in-memory pandas module.
- `data/synthetic_readiness.csv`: 11 input events, including one invalid date;
  10 valid events become 19 daily snapshot rows across seven fictional tails.
- `tests/test_readiness.py`: known-answer, edge-case, consistency, and parity tests.
- `tests/legacy_reference.py`: hash-pinned, allowlisted extraction of pure legacy definitions.
- `run_phase01.py`: test runner and evidence-report generator.
- `TEST_REPORT.md`: actual results, source hashes, command, environment, and limitations.

## Available references and inspection boundary

| Requested source | Finding |
|---|---|
| `streamlit_sql_portal_v3_10_2.py` | Present; parsed in full; readiness constants/functions inspected and isolated |
| `streamlit_sql_portal_v3_10_4.py` | Present; full file has an unterminated string at line 1576; calculation prefix parsed and inspected |
| `streamlit_sql_portal_v3_10_5_corrected.py` | Absent; no claims about its implementation |

In v3_10_2, normalization is at lines 172–287, snapshot logic starts at 360,
fleet metrics at 423, and command metrics at 483. In v3_10_4, corresponding
starts are 184, 373, 436, and 496. File names are not substituted with other
v3_10_5 variants. Hashes in the test harness require re-review if sources change.

The harness compiles only literal constants plus `_first_existing`,
`coalesce_columns`, `build_tail_daily_snapshot`, `compute_jac_daily_metrics`,
and `compute_command_latest_metrics`. It does not import either Streamlit app.
UI calls, imports, configuration loading, CSV/SQL loaders, and ML functions are
excluded. The invalid v3_10_4 UI code is never compiled or executed.

## Status normalization

Values are converted to strings, uppercased, and stripped of surrounding
whitespace. The following exact aliases are then applied:

| Canonical code | Accepted normalized source values |
|---|---|
| FMC | FMC, MC, FULLY MISSION CAPABLE, FULLY_CAPABLE, FULL CAPABLE, MISSION CAPABLE |
| PMCM | PMC, PMCM, PARTIALLY MISSION CAPABLE, PARTIAL CAPABLE |
| PMCS | PMCS |
| NMCS | NMCS, NMC, NON MISSION CAPABLE SUPPLY, NMC-S, NMCS (SUPPLY) |
| NMCM | NMCM |
| DEPOT | DEPOT, DM, DLM, DEPOT MAINT |

Unknown values pass through after case/whitespace normalization. No substring
matching or inference is performed. Python `None` becomes status `NONE`, NumPy
NaN becomes `NAN`, and an empty string remains empty. These are not canonical
statuses, but remain in fleet totals and the serviceability denominator.
Generic `NMC` specifically maps to **NMCS**, preserving the supply classification.

## Input normalization and contract

Use `coalesce_columns` before snapshot construction for raw data. It matches
the legacy column alias lists exactly and ignores header case. Header spaces
are **not** stripped, so `hrs_to_phase ` remains unmatched and `TailNo` is not
an accepted tail alias. The complete alias lists are in `CANDIDATE_COLS`.
Canonical column names take precedence over other aliases.

Dates use `pd.to_datetime(errors='coerce')`; invalid dates are dropped. Date
inference behavior and warnings are retained, not replaced by a new parser.
Inspection/phase hours use numeric coercion. Text attributes are stringified
and stripped, which means null command/reason values may become literal text
such as `None` or `nan`, not missing values.

Supported acceptance inputs have nonblank text tail identifiers, unambiguous
timezone-naive dates, and one command per tail/day. Load tail identifiers as
text to preserve leading zeros; conversion after numeric inference cannot
recover them. Timezone conversion, identifier repair, and mixed-format date
policy have not been introduced. Functions copy inputs rather than mutate them.

## Exact snapshot semantics

1. Require canonical `date`, `tail`, and `status` columns; otherwise return empty.
2. Coerce dates again, discard invalid dates, and normalize statuses again.
3. Normalize each timestamp to its calendar day and find the global maximum day.
4. Group by tail alone, not tail plus platform or command. A tail identifies the
   same aircraft throughout its history and may transfer commands.
5. Sort each tail's events by timestamp and use `groupby('day').last()`.
   This selects the **last non-null value independently for each column**.
   The result can combine attributes from different same-day events.
6. Reindex each tail from its own first recorded day through the global last
   recorded day, inclusive, and forward-fill all attributes. Missing calendar
   days are generated even when no aircraft has an event on that date.
7. Return one row per tail/calendar day. Do not backfill before first appearance,
   extend to wall-clock today, or expire stale statuses.

Equal timestamps lack a business tie-break rule in the legacy code; this phase
does not invent one. Test events at repeated same-day timestamps use different
times. A true null numeric/metadata field can inherit an older non-null value;
a stringified null from normalization does not behave as a pandas missing value.

The implementation uses explicit per-tail iteration in place of deprecated
`GroupBy.apply` behavior. Tested snapshot order, indexes, columns, dtypes, and
values agree with both isolated references in the installed pandas environment.

## Customer-approved business formulas (FINAL)

Let `T` be distinct tails, `F` FMC, `P` PMCM + PMCS, `S` NMCS, `M` NMCM,
and `D` DEPOT in a valid daily snapshot:

```text
Effective denominator = T - S - D
Serviceability %      = 100 * (F + P) / (T - S - D), if denominator > 0; else 0
Availability %        = 100 * (F + P) / T, if T > 0; else 0
```

NMCM is counted separately but **stays in the serviceability denominator**.
Both fleet and command calculations use the same helper and formula.
Metrics consume normalized daily snapshots, not raw event history.
`compute_command_latest_metrics` accepts any requested snapshot date, normalizes
the date argument to midnight, and returns that date's commands in sorted order.
Empty inputs, an absent requested date, or a missing command column return empty.

Fleet counts reconcile with the sum of command counts when every tail has a
command. Fleet availability is weighted by command tail totals; serviceability
is weighted by command effective denominators. Percentages must not be averaged
without those weights. Direct snapshots with true null commands are omitted by
pandas command grouping, matching legacy behavior, so reconciliation is not
guaranteed for malformed/missing-command inputs.

## Resolved legacy documentation error

Both legacy metric docstrings incorrectly describe excluding NMCM as well as
DEPOT and NMCS. The fleet comment also incorrectly says all NMC is excluded.
**The customer-approved executable code uses `total - (nmcs + depot)`**.
Explicit user confirmation resolves this discrepancy: NMCM must remain in
the denominator. No formula change is pending or authorized. Legacy files
remain unchanged; their conflicting comments are historical documentation
errors. Decision [FIS-001](docs/DECISIONS.md) is authoritative for FIS4.

The first synthetic day makes the conflict visible: six tails, three ready,
one NMCS, one NMCM, and one DEPOT produce **75% serviceability and 50%
availability**. Incorrectly excluding NMCM would yield 100% serviceability
and violate the customer-approved formula. The test explicitly requires 75%.

## Known synthetic results

| Day | Tails | FMC | PMC | NMCS | NMCM | DEPOT | Serviceability | Availability |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-01-01 | 6 | 1 | 2 | 1 | 1 | 1 | 75% | 50% |
| 2026-01-02 | 6 | 1 | 2 | 1 | 1 | 1 | 75% | 50% |
| 2026-01-03 | 7 | 3 | 2 | 0 | 1 | 1 | 83.333333% | 71.428571% |

On the final day, command A has three ready tails: 100% serviceability and
availability. Command B has four tails, two ready, one NMCM, and one DEPOT:
66.666667% serviceability and 50% availability. Calculations retain full float
precision; rounding above is for display only.

## Explicit differences and acceptance limits

- **Duplicate snapshot guard:** new metric APIs raise `ValueError` for duplicate
  `(date, tail)` rows, including cross-command duplicates. Legacy APIs use
  distinct tails for totals but count status rows, producing 150% for three FMC
  rows representing two tails. A test reproduces that defect in both references.
  Valid daily snapshots have exact metric parity; no formula was changed.
- **Required-column error:** nonempty malformed metric frames raise a descriptive
  `ValueError` rather than the legacy incidental pandas `KeyError`.
- **No tail groups:** all-null raw grouping keys return an empty snapshot in the
  new module; legacy can fail while reconstructing the date column. Normalized,
  nonblank tail identifiers are the supported contract, not null-key repair.
- **Implementation:** shared metric logic replaces duplication, and per-tail
  iteration avoids relying on pandas' deprecated inclusion of grouping columns.
- **Empty schemas:** legacy-style empty frames are retained; no new fixed empty
  response schema has been introduced.
- **Unverified scope:** full Streamlit runtime behavior, other pandas/Python
  versions, operational data, ML, timezone policy, and equal-time business
  ordering are not part of this baseline acceptance.

Phase 01 acceptance requires all synthetic tests and both available-reference
comparisons to pass, internal fleet/command reconciliation, and unchanged
legacy files. Review `TEST_REPORT.md` for actual evidence. No FastAPI, React,
dependency installation, or packaging is part of this phase.
