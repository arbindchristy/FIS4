# FIS v4 Phase 01 — Legacy readiness baseline

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
