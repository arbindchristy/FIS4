# Phase 03B-2A: historical readiness API

This additive API serves the validated, fictional Phase 03B-1 world. It does not
implement authentication or authorization. Keep local demonstrations bound to
loopback; deployment access control remains a separate acceptance requirement.
There is no real SQL access, prediction, model execution or network dependency.
FIS-001 formulas and FIS-002 single-codebase/offline requirements remain unchanged.

## Explicit selection and startup

```python
from api.main import create_app

app = create_app({
    "mode": "synthetic_history",
    "history": {"as_of": "2026-11-20", "seed": 42017},
})
```

`as_of` is required, strictly YYYY-MM-DD, a real date in 2000..2100. Seed defaults
to 42017 and is a strict integer in 0..2^32-1. No environment/file/secret discovery
occurs. Fleet size and span are fixed to 160 tails, four commands and four calendar
years in this mode; unknown fields are rejected. SQL/history settings are mutually
exclusive and allowed only for their selected mode. Credentials or a SQL connector
are rejected for both synthetic modes. SQL limits, connection factory and no-fallback
behavior are unchanged.

Default `create_app()` / `api.main:app` still selects the small synthetic CSV fixture.
It never generates the large history. Default CSV and SQL applications retain
their original four OpenAPI paths; the history route is not registered in those
modes. The new provider is explicitly selected at application construction, not
by a client query. `source` and X-FIS4-Data-Source remain `synthetic` for both
fictional providers, preserving the existing source enum and response contracts.

For a loopback demonstration using the existing environment, run from FIS4:

```powershell
@'
import uvicorn
from api.main import create_app
uvicorn.run(create_app({"mode": "synthetic_history", "history": {
    "as_of": "2026-11-20", "seed": 42017}}), host="127.0.0.1", port=8000)
'@ | .\.venv\Scripts\python.exe -B -
```

This is a configuration example, not an offline release/start-stop mechanism.
No Node, internet or runtime CDN is needed for the backend. Production/offline
assembly and approved deployment configuration remain separately gated by FIS-002.

## New endpoint contract

`GET /api/v1/readiness/history?date=YYYY-MM-DD[&command=FICTIONAL_A]`

| Parameter | Contract |
|---|---|
| date | Required exact calendar date; end-of-day snapshot; inclusive generated bounds |
| command | Optional one of FICTIONAL_A, FICTIONAL_B, FICTIONAL_C, FICTIONAL_D; no command means entire fleet |

Unknown query keys and duplicate date/command keys are rejected. Read-only GET;
POST returns 405. Response model reuses the existing `FleetResponse` exactly:

```text
{
  "source": "synthetic",
  "date": <requested ISO date>,
  "command": <requested command or null>,
  "metrics": {
    "total_tails": <integer>, "fmc_tails": <integer>, "pmc_tails": <integer>,
    "nmcm_tails": <integer>, "nmcs_tails": <integer>, "depot_tails": <integer>,
    "svc_pct": <number>, "avail_pct": <number>
  }
}
```

The bracketed values above describe types, not fabricated example results.
PMC combines PMCM and PMCS. Canonical status counts/percentages with PMCM/PMCS
separate are also available through the existing status-distribution route in
explicit history mode. All readiness metrics are computed during startup using
the unchanged readiness engine, including NMCM in the serviceability denominator
and both zero-denominator guards. No independent API readiness formula is added.

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/readiness/history?date=2022-11-21'
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/readiness/history?date=2024-11-20&command=FICTIONAL_A'
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/readiness/history?date=2026-11-20'
```

| Outcome | Status / existing error convention |
|---|---|
| Valid day/filter | 200 FleetResponse; fleet 160 tails or selected command 40 |
| Before/after history | 404; detail `No synthetic snapshot for the requested selection` |
| Missing/invalid date, invalid/unknown command, unknown/duplicate keys | 422; safe detail, no arbitrary input echoed |
| Cache unavailable (e.g. lifecycle was not entered) | 503; detail `Synthetic history unavailable`; no fallback |
| Route in CSV or SQL mode | 404; no history initialization, SQL query or synthetic substitution |
| Unexpected application error | Existing generic 500 response convention |

Existing endpoints retain their paths, query/response models and error conventions.
In explicitly selected history mode only, their data comes from the same history
cache: optional date still defaults to the as-of date; unknown well-formed command
still gives 404. The new historical endpoint requires a date and rejects unknown
commands with 422. Default fixture/SQL behavior is unchanged. `/health` remains
liveness only, with its existing response, not an authentication/readiness promise.

## Provider and cache architecture

`SyntheticHistoryProvider` structurally implements `DataProvider`: its source is
`synthetic`, and `load_events()` returns a defensive copy of validated
readiness events. Its additional `read(day, command)` returns a frozen
DailyReadiness record; `metrics()` returns a fresh scalar dictionary. Dates and
commands are immutable values. No mutable frame or internal mapping is exposed
through HTTP. Retained events are private to the provider and copied on access.

FastAPI lifespan explicitly initializes the selected history provider in a worker
thread before serving. A per-provider lock serializes initialization and atomically
publishes one complete cache. Concurrent initialize calls do not regenerate it.
No global cache, lazy request-time initialization, client-supplied cache keys,
background refresh or unbounded eviction map is used.

The unchanged simulator generates and validates one full world. Cache preparation
uses its existing snapshot and calls the approved daily metrics function once
for the fleet and once for each command subset. Status distributions are grouped
once. A read-only mapping holds five records per day (7,305 for this cutoff),
each with six canonical status counts and existing readiness metrics. Coverage
and cardinality are checked before publication. The snapshot, operational features
and episode/action tables are released; only immutable aggregates and private
readiness events remain. Bounds are fixed independently of unchanged SQL limits.

Simple historical and existing aggregate requests in history mode perform dictionary
lookups/response formatting: no generation, CSV/SQL reads, full-history snapshots
or DataFrame aggregation. Repeated and concurrent API tests patch the generation/
readiness computation functions to fail if called after startup.

Shutdown clears that provider's cache. A later successful lifecycle on the same
app initializes a fresh world once. Instances/configurations have separate locks
and caches. An in-flight read may finish using its immutable record while shutdown
releases the provider reference. Initialization failure publishes no partial cache,
exposes only HistoryUnavailable, fails startup and is sticky for that provider;
retry requires a newly constructed application. There is no fixture fallback or
implicit retry on request. Lifespan must be enabled by the hosting server.

## Verification and measurement scope

`tests/test_history_api.py` adds 22 portable tests. One full real synthetic world
is prepared per suite; lifecycle/concurrency/error tests reuse defensive fixture
copies of its immutable aggregates to avoid repeatedly generating identical worlds.
The separate benchmark uses actual application startup and actual generation.
No SQL Server is connected; SQL isolation tests use injected connector mocks.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_history_api.py -v
.\.venv\Scripts\python.exe -B scripts\benchmark_history.py --requests 30
.\.venv\Scripts\python.exe -B scripts\benchmark_history.py --requests 30 --profile
```

Benchmark cold time includes app construction/lifespan generation, validation and
aggregate preparation. It excludes earlier interpreter/API import time. Warm
measurements include in-process TestClient/ASGI/thread-dispatch/validation/JSON
overhead: three dates, fleet plus FICTIONAL_A, 30 sequential requests each. They
are not socket/TCP/TLS, authorization, multi-user load or production latency
benchmarks. Profiling reports Python allocation peak and current allocations
after startup/GC, not OS working set/RSS or all native allocations. It includes
lazy simulator imports/retained Python state and adds timing overhead. See current
PROJECT_STATE for actual numbers, commands, security findings and deferred risks.
