# Phase 05A: exact-date NMCS preparation contract

Recorded 2026-11-24 (Asia/Dubai). This phase implements offline feature/label
preparation, not a predictor, score, rule engine, API or frontend. The explicit
Phase 05A customer instruction establishes a new NMCS occupancy experiment;
it does not relabel, retrain or replace legacy Enhanced1 combined-NMC inference.
FIS-001/FIS-002/FIS-003 and the original readiness/source contracts remain intact.

## Baseline and evidence

Expected main d4d11b46dbf7541362b6bd49d13543342c29057a contains merged PR #14.
Live origin/main advanced to 1565e7b82c09e9bd263f29e8c8ae292d1b5eeee6:
one commit, README title only (one insertion/deletion). This was reported before
implementation. Branch feature/05a-nmcs-foundation starts at that current main.
Existing untracked patches/launcher, deployment worktree and raw evidence remain
untouched. No dependencies installed, model loaded, SQL accessed or image rebuilt.

Sources inspected: simulator/contracts.py and generator.py, readiness.py,
api/providers.py, STREAMLIT_PARITY.md and INTRANET_INTEGRATION_CONTRACT.md.
No restricted view definition, original operational rows or artifact was opened.

## Source interpretation and normalization boundary

| Source | Verified meaning | Prediction consequence |
|---|---|---|
| Existing simulator events | Initial state, changes and final boundary per tail; multiple updates possible only by caller fixtures | Sparse state changes, not independent daily reports |
| Validated simulator snapshot | Daily reconstruction already checked against readiness engine | Fictional state persistence may explicitly validate carry days |
| Simulator operations | Daily as-of utilization and inspection balance | Inspection is available for a future explicit adapter; no phase-hours field exists |
| Approved production history contract | Customer-established working-day observations for all active aircraft, sometimes multiple updates/day; joins current assignments | Not independently verified against SQL; do not reinterpret as sparse onset events |
| Current CSV/SQL provider | Four-column events; SQL placeholder and mocked access | Not an implemented adapter for the approved nine-column view or this pipeline |

The nine logical view aliases remain date, platform, tail, status, command,
hrs_to_insp, hrs_to_phase, location and reason. Timestamp precision, source calendar,
physical mappings, active population, current joins and the exact approved hours
COALESCE behavior still need sanitized evidence. No new physical column is assumed.
Location/reason are not consumed by this phase. No adapter or source change.

`prediction.nmcs.Observation` accepts already normalized naive source-calendar
datetime, nonempty trimmed **text** tail/command/platform and one of six canonical
statuses. Tail is never cast to integer; leading zeros survive. Raw aliases,
invalid dates/timezones, invalid statuses and ambiguous generic NMC fail closed.
The existing readiness alias rules are unchanged; upstream normalization of a real
feed for NMCS-only labels needs source approval, particularly generic NMC ambiguity.
Hours are independent finite numbers or None, including valid negative overdue
balances. Missing hours stay None with separate missingness flags, never zero-filled.
No new imputation overrides the existing view's COALESCE requirements.

`reconstruct(records, cutoff=..., validated_reconstruction=False)`:

1. Exclude observations after explicit validated-data cutoff before content and
   ownership validation. No automatic wall-clock cutoff. Reject malformed timestamps.
2. Sort tail/timestamp; identical duplicate records collapse. Conflicting records at
   exactly the same timestamp fail; input order is not an invented tie-breaker.
3. Require stable command/platform per tail in this extraction. Conflicts fail.
   Current assignments are authoritative; no historical transfers are fabricated.
4. Collapse intraday updates using latest non-null values per column, then carry
   forward through the latest visible global observation day. No pre-first-day
   backfill and no extension to today/cutoff beyond visible history.
5. Each daily row records observed versus carried and usable versus unvalidated.
   Default gap rows are **unusable** for labels and features, even though last-known
   status remains explicit. `validated_reconstruction=True` is an explicit caller
   attestation that carry-forward is accepted for this dataset, not inferred approval.

This matches documented readiness reconstruction on valid normalized fictional
inputs (including partial-null hours, intraday changes and missing weekends).
It is not a replacement for readiness or Enhanced1's different whole-row/per-tail
reconstruction. Unsupported raw/source ambiguities fail instead of silently repairing
legacy behavior. The immutable tuples/read-only index are prepared once and reused.

## Exact target contract

`target_at(history, tail, observation_date, horizon_days)` returns an immutable
Target with exact reference/target dates, offset, nullable value, reason and
observed/validated_carry provenance. H must be an integer 1..180 (bool rejected).

Y(tail,T,H) = 1 if usable daily status at T+H is NMCS; otherwise 0 **only if that
status is usable**. NMCM, FMC, PMCM, PMCS and DEPOT are negative for NMCS occupancy.
This is neither occurrence anywhere in (T,T+H] nor exact onset prediction. Current
NMCS aircraft remain eligible. Missing reference/target or outcomes after cutoff
return null with reference_unavailable, target_unavailable or after_cutoff.
No missing outcome is filled as non-NMCS. Dates use calendar arithmetic, including
leap days. An incomplete target horizon is not eligible for training/evaluation.

PR #15 correction: target_at, label_coverage and features_at share reference_at.
A reference date must have at least one fleet observation on that calendar date
within the validated cutoff, plus a usable state for the requested tail. A different
tail's same-day observation can establish the visible global endpoint; explicitly
validated tail carry is still allowed. Later observations cannot make an earlier
fleet-wide gap reference eligible. Target dates may still use explicitly validated
carry: outcome availability and prediction-time reference eligibility are distinct.
Immutable observation-date membership is indexed once, not rebuilt per label.

## Feature contract and leakage boundaries

`features_at(history, tail, reference_date)` returns a separate dictionary with no
tail numeric feature, target, label or battalion field. Targets never enter this
payload. Feature metadata contains exact reference, effective cutoff and requested/
available history dates. Default requested reference is six calendar years ending
T inclusive (day after prior anniversary); it does not claim six years are present.
Future raw observations cannot extend the feature-visible global endpoint.
Only immutable daily rows at or before T are inspected; no per-query fleet rebuild.
Rolling-window episode starts inspect the immediately preceding usable day from
history, then count only starts whose dates lie in the requested window. An NMCS
first window day preceded by usable non-NMCS counts once. Pre-existing NMCS or an
unknown/unusable predecessor does not establish a new start. The lookbehind does
not add an extra day to the window population, duration or NMCS-day count.

| Feature group | Definition / explicit absence |
|---|---|
| Context | Current command/platform/status text, not fitted encodings or historical ownership claims |
| Planning | Separate inspection and phase hours plus missing flags; no inferred phase from inspection |
| 30/90/180/365 windows | Inclusive T-W+1..T, expected/usable days, completeness; NMCS days/known starts are null unless full window usable |
| NMCS episodes | Consecutive usable NMCS days form one run, repeated reports do not add episodes; gaps break runs and censor boundaries |
| Durations/recovery | Completed, known-start-and-recovery NMCS durations and mean; persistent/open/left-censored runs excluded from completed statistics |
| Recurrence | Mean known-start intervals only when entire interval is usable; not latent generator fault recurrences |
| Days since | Last known NMCS diagnostic; exact days-since is null if no known NMCS or unknown intervening days |
| Current state | Consecutive known duration lower bound with left-censor flag |
| Transitions | Adjacent usable daily state changes only; do not bridge unknown gaps |
| Long history | Available/usable days, completeness, fragment/known-start/censor counts over bounded six-year reference (configurable 1..10 years) |

No future sampled repair duration, receipt, CLOSE action, episode closed_at, latent
fault state, eventual target or future statistics is used. Features may include
observed NMCM as current context/previous transition, never as the NMCS label.
Window counts and history completeness expose insufficient coverage rather than
pretend missing days are healthy. No scaler, one-hot vocabulary or imputer is fit.
Future preprocessing must be fit on training folds only. Rules and ML assessments
must remain independent in later implementation; neither is implemented here.

Current assignment context is safe for the fixed fictional world, but real data
extracted with current-at-extraction assignments cannot prove prediction-time known
command associations. Do not claim a leakage-free operational backtest without
assignment/extraction evidence. Rejecting within-extraction changes cannot solve it.

## Actual fictional feasibility assessment

Command: `.venv/Scripts/python.exe -B scripts/assess_nmcs.py` (exit 0).
Seed 42017/as-of 2026-11-20; unchanged generator, one generation only, 16.32 seconds
for the original generation, validation and assessment on this laptop.
The PR #15 corrected reassessment exited 0 in 15.621 seconds, saved separately in
`.harness-test-tmp/phase05a-review-feasibility.json`; original evidence is retained. No memory benchmark or
Render/Windows inference timing is implied. Local ignored evidence:
`.harness-test-tmp/phase05a-feasibility.json` (PowerShell UTF-16 redirected JSON).
The script prints aggregate JSON only; no rows/artifacts are exported or committed.

Coverage: 2022-11-21..2026-11-20 inclusive, 1,461 days, 160 tails, four commands,
233,760 tail-days, 10,273 sparse change/boundary records, **872 NMCS runs**.
Zero initially left-censored NMCS runs. These are separate temporal episodes,
not 872 statistically independent/IID failures or fitted operational observations.
Adjacent labels and offsets are strongly correlated.

With explicit validated synthetic carry **and as-of reference eligibility**, the
corrected eligible examples for every H in 1..180 are exactly
`160 * (1460 - H)` for this measured dataset only. One fleet-wide observation-gap
reference day is excluded: **160 fewer examples at each of all 180 horizons**.
The former `160 * (1461 - H)` formula is superseded; it counted references that
could not produce as-of-safe features. Fleet size and historical coverage did not
change. The script and label_coverage enumerate counts without materializing
42 million overlapping target objects. Corrected actual counts:

| H (days) | Eligible tail/reference-date pairs | NMCS positives |
|---|---:|---:|
| 1 | 233,440 | 8,132 |
| 7 | 232,480 | 8,103 |
| 30 | 228,800 | 7,995 |
| 90 | 219,200 | 7,602 |
| 180 | 204,800 | 7,028 |

The event-only projection contains no hours: this report makes no claim of complete
inspection/phase feature availability. Inspection can later join validated daily
operations by tail/day; phase is genuinely unavailable in the current synthetic
schema and must not be invented. No latent episode tables enter the projection.

Four years is sufficient for pipeline/model *experiments*, not six-year product
acceptance or accuracy/probability claims. Proposed temporal partitions: first two
years training, third validation, fourth locked test. For each H, require T+H < next
partition start; purge cross-boundary labels (up to 180 days), retain as-of-safe
historical features, and fit transforms within training only. The long horizon
leaves fewer independent reference periods in one-year holdouts. Evaluate class
imbalance, persistent-NMCS baseline, calendar seasonality, calibration and episode/
tail clustering, not random row splits. Use additional fictional seeds/held-out
tails as robustness checks; none was trained or evaluated here.

A separate six-year fictional world can use the existing supported
`SimulationConfig(as_of=date(2026,11,20), seed=42017, years=6)`, generated offline
into a new ignored location with its own schema/config/source manifest. This is a
proposal, **not executed**; do not change the dashboard's four-year default or
generator algorithm. Changed start date creates a different simulation, not an
extension of the existing world. Six years provides 350,560 tail-days for this
cutoff, but episode counts/performance must be measured, not extrapolated.

## Verification and release implications

Focused tests: `tests/test_nmcs.py` covers all ten customer requirements, canonical
negative statuses, all 180 offsets, exact-day versus onset distinction, duplicates,
partial-null intraday values, missing weekends, ownership conflicts/leading zeros,
cutoff/feature leakage, current NMCS, left/right censoring, deterministic input order,
and coverage counts independently checked against individual `target_at` labels.
Reconstruction parity imports the unchanged readiness engine on fictional fixtures.
Six added PR #15 regressions reproduce both review defects: the pre-fix 41-test
run fails 19 assertions; corrected focused tests pass 41/41. They cross-check all
180 coverage horizons against featureable references, preserve future isolation,
and cover known, ongoing and unknown-predecessor window boundaries across the
four supported windows. Exact commands/results are recorded in PROJECT_STATE.md.

Foundation code uses Python standard library only. The assessment/parity tests reuse
already pinned pandas/simulator dependencies. No Windows/Linux runtime pin changes,
joblib/scikit-learn/model dependency, operational data or authentication claim.
Production modules do not import this package; existing Docker allowlist excludes
prediction, tests and this assessment script. Render startup/image are unchanged.

Phase 05B recommendation: **CONDITIONAL GO for separately approved offline fictional
NMCS occupancy model experiments**, not legacy inference/customer release. First
freeze feature schema, hours availability and preprocessing; approve exact compatible
Windows/Linux training/runtime dependencies; prepare six-year data; implement purged
temporal partitions and independent evaluation against naive occupancy baselines.
Report per-horizon discrimination, calibration and uncertainty before any accuracy
or probability claim. Aircraft features support later platform/command/fleet grouping,
but no population forecasting, aggregation of probabilities or UI is implemented.

Blocking real-source evidence: source calendar/timezone, same-time ordering key,
canonical/ambiguous statuses, completeness/staleness of observed/carry targets,
active-tail/retirement population and current assignment attribution, physical field
mapping and hours COALESCE/defaults. These block SQL/operational prediction acceptance,
not the explicit fictional pure-data foundation. Legacy artifact/trainer compatibility
remains unresolved and is not required to relabel or reuse it for this new target.

Any later customer ML release requires a fresh Linux dependency, memory, cold-start
and functional assessment and separate Windows x64 offline exact-package acceptance.
No inference, NMCM prediction, SQL, frontend, Render deployment or model artifact is
authorized or delivered by this foundation. Public training data/artifacts must
remain wholly fictional and receive a separate exposure review.
