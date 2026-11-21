# Phase 03B Task 1: fictional fleet history, schema v1

This generator uses invented engineering assumptions and identifiers. It is not
an aircraft reliability model, operational evidence, or a validated predictor.
No databases, files from the legacy project, external services, models or new
dependencies are used. Existing API endpoints, synthetic fixture, provider
selection and React dashboard are unchanged. FIS-001 and FIS-002 still apply.

## Running locally

From the FIS4 workspace, using the existing pinned Python environment:

```powershell
.\.venv\Scripts\python.exe -B -m simulator --as-of 2026-11-20
.\.venv\Scripts\python.exe -B -m simulator --as-of 2026-11-20 --profile
# Optional export to a NEW ignored workspace directory; never overwrites:
.\.venv\Scripts\python.exe -B -m simulator --as-of 2026-11-20 --export
```

Defaults: seed 42017, 160 tails, four calendar years, four balanced commands
FICTIONAL_A through FICTIONAL_D. The as-of date is required, with no wall-clock
default. The example interval is 2022-11-21 through 2026-11-20 inclusive: 1,461
days and 233,760 aircraft-days. Start is the day after the prior anniversary;
February 29 anniversaries use February 28 in non-leap years. CLI options
`--seed`, `--tails`, `--years` configure generation. Tails must be divisible by
four, 4..1600; years 1..10; seed an integer 0..2^32-1; as-of year 2000..2100.
The projected history is capped at 3,000,000 aircraft-days. These are guardrails,
not a performance guarantee at the maximum configuration.

```python
from datetime import date
from simulator import SimulationConfig, generate

history = generate(SimulationConfig(as_of=date(2026, 11, 20)))
observed = history.features_at(date(2025, 6, 1))
events = history.load_events()  # Defensive copy; existing DataProvider shape.
```

Generation returns validated DataFrames in memory. Export writes six CSV tables
and manifest.json under `.harness-test-tmp/synthetic-ASOF-SEED-TAILS-YEARS/`.
It refuses an existing directory. The manifest identifies schema version, source,
seed, dates, sizes and SHA-256 hashes. It omits timings/machine paths so output is
repeatable. Generated tables remain ignored and must not be added to Git.
Re-import CSV identifiers with `dtype={"tail": str, "episode_id": str,
"active_episode": str}`, `keep_default_na=False`, and parse documented timestamps
explicitly; empty closed_at means a right-censored episode, not a planned date.
CSV generation is optional and not part of dashboard startup.

## Generation model and time semantics

Each aircraft has a private RNG derived from the seed and its fixed index;
global random state is untouched. Generation order is deterministic. Repeatability
means identical configuration, schema/algorithm version and supported runtime;
it is not a promise across future algorithm, Python or pandas changes. Adding
aircraft does not change earlier aircraft RNG streams. Changing the cutoff also
changes the start of a fixed-length history, so shifted windows are separate
simulations, not continuation/replay of one persisted world.

Aircraft begin with invented lifetime hours and staggered inspection balances.
One flight opportunity per day adds 0.5..4.0 hours when FMC/PMC permits it;
partial capability reduces flight probability. Flight time is capped at hours
remaining, accumulated in integer tenths internally. NMCS, NMCM and DEPOT
aircraft never fly. An inspection begins on the next day after the balance reaches
zero, persists for 2..5 days and resets the 240-hour interval on completion.

Fault onset probability depends imperfectly on command environmental stress,
accumulated flight hours and inspection proximity. Faults use four fictional
component families; previous faults can recur, with an additional bias toward
the last family. A recurring flag means the family has already occurred on that
aircraft. Cumulative and recurring counts include only faults already opened.

Each fault has fixed major/minor severity for its episode. A demand, if needed,
is for one fictional spare associated with that fault family. PART_REQUEST opens
the demand; PART_RECEIPT closes it after a positive delay, followed by positive
repair time. Major faults progress NMCS -> NMCM -> FMC; minor faults progress
PMCS -> PMCM -> FMC. Faults without a demand begin in NMCM or PMCM. Repair cannot
finish before receipt. Episodes persist across days, rather than redrawing daily
statuses. There is at most one active episode per tail; overlapping discrepancies,
multi-part demands and transfers are outside v1.

Four documented fictional profiles vary flying probability (0.55..0.85), stress
(0.85..1.35), maximum supply delay (10..24 days) and repair duration (1..10 days).
These are assumptions, not fitted operational distributions. Delays and repair
durations also contain noise. Depot entries are staggered (first due after
80..650 days), persist 30..65 days and recur after another 550..750 days following
exit. Depot completion resets inspections but never reduces lifetime hours.
Pending depot work takes priority over a new inspection/fault; active work is
completed first. Long episodes opened near as-of remain unresolved/censored.

All timestamps are timezone-naive **fictional simulation time**, consistent with
the existing readiness contract. At a day boundary, part receipt occurs at 00:00,
episode close at 00:01, new open at 00:02 and part request at 00:03. The status
used for that day's flight opportunity is emitted at 23:59:59 on a change, plus
an initial and final coverage marker for every tail. There are no competing
equal-time status events. Markers can repeat a previous status. Event history
describes end-of-day readiness, not intraday dispatch states. Daily operational
rows are keyed by midnight dates and contain the day's observed closing balance.

## Explicit relational contracts

Every table is source=synthetic in the containing history/manifest. Tail is an
opaque six-character text key, e.g. `000001`; never an integer. Dates are
`datetime64[ns]` in memory; CSV uses ISO `YYYY-MM-DDTHH:MM:SS`. SQL compatibility
means explicit string keys, scalar fields and normalized parent/child relations;
no SQL objects or mappings are provisioned here. A future mapping should use
VARCHAR keys, DATETIME2 for timestamps, DECIMAL(12,1) for hours, INT counters and
BIT flags, with appropriate indexes/foreign keys and separate synthetic provenance.

| Table / key | Fields and meaning |
|---|---|
| aircraft / tail | tail TEXT; command TEXT; initial_hours FLOAT hours; inspection_interval FLOAT hours; initial_hrs_to_insp FLOAT hours. Exactly one command throughout v1. |
| events / (date, tail) | date TIMESTAMP; tail TEXT FK aircraft; status TEXT enum FMC/PMCM/PMCS/NMCS/NMCM/DEPOT; command TEXT. Exact existing provider readiness-event columns. |
| operations / (date, tail) | date daily TIMESTAMP; tail TEXT FK aircraft; flight_hours, total_hours, hrs_to_insp FLOAT hours; fault_count, recurring_fault_count INT; active_episode TEXT FK episodes or empty; episode_age_days INT; supply_wait_days INT; outstanding_demand INT 0/1. Age is elapsed whole days, 0 on opening day; supply wait resets to 0 after receipt. |
| episodes / episode_id | episode_id TEXT `SYN-TAIL-SEQUENCE`; tail TEXT FK aircraft; kind TEXT enum FAULT/INSPECTION/DEPOT; fault_code TEXT fictional family or empty; recurring BOOL; opened_at TIMESTAMP; closed_at nullable TIMESTAMP actual observed close only. |
| actions / (episode_id, action) | date TIMESTAMP; episode_id TEXT FK episodes; action TEXT enum OPEN/PART_REQUEST/PART_RECEIPT/CLOSE. At most one of each per episode; OPEN required, other actions only when observed. |
| snapshot / (date, tail) | date daily TIMESTAMP; tail TEXT; status TEXT; command TEXT. Built using unchanged readiness.coalesce_columns and build_tail_daily_snapshot, then sorted by date/tail. |

Schemas are executable in `simulator/contracts.py`. `validate()` checks exact
columns, population/commands, identifiers, complete daily coverage, chronology,
timestamp conflicts, event bounds, snapshot equality with the approved engine,
flight accumulation/grounding, inspection consumption/resets/due entry, action
keys/timing, non-overlapping active episodes, recurrence and cumulative counts,
supply-state features, depot/inspection statuses and persistent transitions.
No readiness percentage is computed in the generator. Reconciliation tests call
the original fleet/command engine. These integrity checks do not establish
real-world physical accuracy or statistical model usefulness.

## Prediction-date boundary

`features_at(day)` returns only that day's observed operations plus readiness
snapshot. Its cutoff is **end of that day**; use it only for strictly later
targets. The function never reads episode closed_at, future actions, sampled
durations, planned receipt or eventual repair outcomes. Latent durations remain
private generator state and are absent from exports. For retrospective training,
episode closed_at and receipt/CLOSE actions after a prediction date are outcomes,
not features. This is essential even though the complete history is synthetic.

Use chronological train/validation/test partitions and fit transformations on the
training portion only. Future target construction must handle censored outcomes
and split boundaries, avoid using contemporaneous NMCS/NMCM as a future label,
and use only rows available at the chosen cutoff. This task builds no labels,
ML training, rule engine, inference code or prediction endpoints.

## Efficient future FastAPI integration proposal

Generate/version/validate an artifact once in an explicit preparation step.
Load it once per process using a bounded lifecycle cache keyed by version/seed/
as-of/schema. The history structurally implements the existing DataProvider
interface (`source`, `load_events`) but is deliberately not selected or imported
by the production API. Do not call generate() or rebuild the four-year snapshot
on a dashboard request.

A separately reviewed integration can retain the precomputed daily snapshot,
index date/command selections and precompute fleet/command/distribution aggregates
with the existing readiness engine. Return existing API contracts from those
cached aggregates, including the configured synthetic source. A SQL-compatible
future artifact could store the normalized tables and indexed daily/aggregate
materializations. Define provenance, row/span bounds and invalidation before
integration: existing provider bounds/configuration must not be silently expanded.
Large Python object-string frames are convenient for Task 1, not a promised
production storage format. Measure per-worker memory and startup before choosing
categoricals/columnar persistence in a separately authorized phase.

Actual commands, tests, performance/memory evidence, security dispositions and
remaining acceptance boundaries are recorded in PROJECT_STATE.md.
