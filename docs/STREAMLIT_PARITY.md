# Streamlit parity contract

Status: Phase 03C-0 documentation approved by the chief architect on 2026-11-22.
Prediction compatibility, physical SQL verification and deployment acceptance remain unverified.
Recorded 2026-11-22. See [FIS-001/FIS-002/FIS-003](DECISIONS.md) and
[the integration contract](INTRANET_INTEGRATION_CONTRACT.md).

## Authority and evidence

The customer identifies working intranet Streamlit v3.10.4 and
`VW_MNT_AIRCRAFT_HISTORY` as the functional and source baseline. Preserve them;
do not substitute another view, trainer or business interpretation without
explicit approval. This document distinguishes customer-established requirements,
static observations of local reference files, and unresolved compatibility checks.
It does not certify deployed SQL schema, model performance or an executed intranet test.

Local reference sources, inspected read-only under the legacy project:

| Reference | Local identity and evidence |
|---|---|
| Streamlit | `streamlit_sql_portal_v3_10_4.py`; SHA-256 `6b1ef3451ec9a47203cf96d1cd7a83bb872ed64bd3bce523c9c744ca4be06980` |
| Enhanced1 | `Genspark Nov 2026/train_nmcs_model_enhanced1.py`; SHA-256 `8022ac3164cac71d6d014aaa38dae553de3346149c3dd5e55974584ecec4d51d` |
| Requested trainer spelling | `train_nmcs_mode_enhanced1.py` was not found in the inspected legacy inventory; the located filename contains `model` |
| Artifact | `nmcs_model_7d.joblib` filename exists; contents, provenance, dependency versions and actual producing trainer were not inspected |
| View | Logical identity and current-assignment/active-tail behavior supplied by the customer; restricted DDL was not accessed or copied |

The local sanitized Streamlit file fails static parsing at line 1576 in an icon
fallback expression. This does not invalidate the customer-confirmed working
intranet application. No local damage was repaired. Additional local feature-code
issues are recorded below, not generalized to the deployed application. Enhanced1
passes static syntax parsing; parsing is not execution or performance evidence.
No reference module was imported and no model was loaded.

## Logical source and organization

The unchanged history view joins aircraft observations to current aircraft and
organizational assignments and applies its existing active-tail filtering.
Production Control records all active aircraft on working days, sometimes multiple
times daily. These are customer-established source requirements, not observations
from a database query. Do not reinterpret the feed as sparse fault-onset events.

The authoritative hierarchy is Parent Force -> Command Unit -> Battalion -> Tail.
Current assignments are authoritative; historical assignments are unavailable.
Consequently an older status grouped by command is attributed through the current
assignment supplied by the view. It is not evidence of historical command ownership.
Do not invent transfers, infer assignments from platform, or independently change
active-tail filtering. Exact active criteria and join cardinalities need approved
sanitized schema evidence before integration.

Battalion is internal mapping only. Never serialize its identifiers, names or
relationships into ordinary UI/API responses. Platform is an aircraft attribute
and independent analytical dimension, not an organizational level. Verified
command/platform associations must come from the selected provider.

## Normalization and daily reconstruction

Readiness daily reconstruction follows the established Streamlit behavior
documented in this section. Enhanced1 prediction reconstruction remains a distinct
compatibility requirement, documented separately below. Do not silently unify
their algorithms or use prediction reconstruction to redefine readiness history.

Static source anchors: `coalesce_columns` (256), `build_tail_daily_snapshot` (373),
`compute_jac_daily_metrics` (436), `compute_command_latest_metrics` (496).
Line numbers identify the fingerprinted local copy, not deployed source versions.

1. Column matching is case-insensitive and selects the first recognized alias;
   Streamlit does not trim header whitespace before alias matching.
2. Dates use pandas datetime coercion; invalid observations are removed. No
   explicit source timezone conversion is implemented in this path. Confirm the
   source time basis and calendar boundaries rather than introducing conversion.
3. Inspection/phase values use numeric coercion. Status becomes uppercase stripped
   text, then the existing alias mapping is applied. PMC maps to PMCM; generic
   NMC maps to NMCS. Unknown status text is retained, not silently reassigned.
4. Tail, platform, command, location and reason are stripped string values.
   Stringification of nulls is part of the inspected legacy behavior; it is not a
   new data-cleaning recommendation. The original CSV loader infers types first,
   so it can lose leading zeros. Provider ingestion must retain text identifiers.
5. Sort by tail and observation timestamp before constructing calendar days.
   Group by tail/day and take pandas `last()`: last non-null value **per column**,
   not necessarily one complete final observation. Preserve that distinction.
6. Reindex each tail from its first observed day through the global latest
   observed day, inclusive, then forward-fill. This includes weekends, holidays
   and missing working days. Do not backfill before a tail's first observation,
   extend to wall-clock today, invent a staleness expiry, or interpolate statuses.
7. Latest fleet date is the maximum reconstructed observation date. Historical
   population is the distinct tails present on that day after reconstruction;
   no fixed fleet size is imposed by Streamlit. The source's current active filter
   limits which tails can appear anywhere in the extracted history.

A missing day means carried-forward last-known status, not FMC, zero activity or
an extra observed report. Equal-timestamp conflicting observations lack a verified
business tie-breaker. Do not invent one; resolve with sanitized source evidence.
Raw duplicate rows must not inflate distinct-tail readiness. FIS4 validates daily
snapshot uniqueness before metrics; its approved regression expectations remain locked.

## Readiness, occurrences and filters

Canonical statuses: FMC, PMCM, PMCS, NMCS, NMCM, DEPOT. PMC = PMCM + PMCS.
NMCS means Non-Mission Capable due to Supply; NMCM means Non-Mission Capable due
to Maintenance. These remain separate statuses even where prediction combines NMC.

FIS-001 is FINAL for fleet and every command calculation:

```text
Serviceability (%) = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
Availability (%)   = (FMC + PMCM + PMCS) / Total * 100
```

Total is distinct tails in a valid daily snapshot. NMCM stays in the
serviceability denominator. A nonpositive applicable denominator returns 0%.
Incorrect legacy comments suggesting NMCM exclusion have no authority.

Historical NMC counts in feature windows count reconstructed aircraft-days in
those statuses, including persistence across filled days. They are not independent
failures, supply requests, repairs or episode onsets. Repeat daily observations
of an unchanged status do not define separate failures.

The local overview and command comparison use the latest data date. NMCS Insights
has its own date selector and groups distinct tails by reason/command/platform.
Despite its docstring mentioning both statuses, `nmcs_reason_summary` (556) filters
NMCS only; absent/empty reasons become Unspecified. Preserve the distinction from
combined-NMC prediction. Prediction drilldown offers command multi-selection and
risk band; an empty command selection does not filter. Platform is displayed and
used in reason grouping, but no global platform selector was found in this copy.
Do not describe planned platform filtering as existing global-filter parity.

Legacy trend selection uses date >= latest minus lookback days; the inclusive
boundary can produce lookback + 1 observations. Current FIS4 series contracts use
exact inclusive 30/90/180/365-point windows, clipped at available start. This is a
recorded contract difference, not authorization to change either existing route.

## Enhanced1 training contract: statically verified

Input requires `date`, `platform`, `tail`, `status`, `command`, `hrs_to_insp`,
`hrs_to_phase`. Extra fields, including location/reason, are discarded. Header
BOM/whitespace/case normalization differs from Streamlit. The loader requests
string types for named categorical columns before header normalization; verify
leading-zero preservation for aliased, BOM-prefixed and differently cased headers.
Dates/hours are coerced; missing date/tail rows are dropped. Canonical status text
is uppercased/stripped; the full readiness alias map is not applied here.

Enhanced1 daily reconstruction (121) stably sorts timestamps, normalizes days,
keeps the last **whole row** per day and forward-fills to each tail's own final
day. This differs from Streamlit's per-column last/global-end reconstruction.
Do not silently unify those algorithms or substitute one for the readiness engine.

The CLI supports horizon 7 or 30 days (default 7). At date T, the target is any
NMCS or NMCM day in T+1 through T+H, excluding T. A complete future window is
required; incomplete labels become censored and are excluded. Training eligibility
is currently FMC, PMCM, PMCS or DEPOT, excluding currently NMCS/NMCM. The artifact
metadata calls this `new_onset_nmc`; it is a combined NMC target, not separate
supply/maintenance probabilities or time-to-recovery. DEPOT eligibility is actual
source behavior and must not be silently removed.

Features are computed before eligibility filtering, using history through T:

- Current hours to inspection and phase.
- Days since the first available observation; this is dataset age, not aircraft age.
- Days since the latest reconstructed NMCS/NMCM day, including T; 9999 before any.
- Time-based rolling 90-day combined NMC-day count, using pandas window semantics.
- One-hot current status and command. Platform is input context but not encoded
  in this feature matrix. Tail and battalion are not feature columns.

Numeric infinities become missing, then 0.0; numeric features become floats.
Current status and rolling history can therefore describe persistent downtime.
Current command encodings cannot establish historically known organizational
assignments; prediction-date leakage/attribution limitations must be disclosed.

Evaluation (280) uses an approximately 80% chronological date cutoff: training
rows must satisfy T+H < cutoff; holdout dates are >= cutoff. It prints classification
metrics and ROC AUC when classes permit, then refits on all eligible rows.
Estimator settings: logistic regression, lbfgs, max_iter 1000, n_jobs 1, balanced
class weights. No evaluation outputs, calibration or operational validity were
verified. Do not claim validated probabilities or guaranteed event rates.

Output bundle keys: `estimator`, `feature_columns`, `horizon_days`, `schema_version`
(2), `target`, `nmc_codes`, `window`, `eligible_statuses`, `history_end`.
The output path is a CLI argument; the existing artifact's filename alone does
not prove it was produced by this exact trainer, target or seven-day configuration.

## Streamlit rules, inference and compatibility checks

Static rule code (650) uses recent combined-NMC counts: add 0.50 for >=1 in
7 days; otherwise 0.35 for >=2 in 30 days; otherwise 0.25 for >=3 in 90 days.
Currently NMCS/NMCM sets a minimum of 0.90; PMC adds 0.10. Minimum historical
inspection/phase balance <50 adds 0.25, otherwise <100 adds 0.15. Clamp to 0..1;
HIGH >=0.70, MEDIUM >=0.40, otherwise SAFE. This is a heuristic score, not ML
probability. The rule path includes currently NMC tails, unlike Enhanced1 training.

The local feature builder (589) contains a malformed status-mask expression and
an undefined combined mask. It also differs from Enhanced1: recent 7/30/90 counts,
90-day inspection minima (slice can span 91 inclusive days), six status flags,
and no command one-hot/time-since features. These are local discrepancies requiring
sanitized working-intranet feature evidence, not permission to repair or retrain.

Inference (759 and 1690+) accepts estimator/model keys and feature-column aliases,
reorders columns, fills absent columns with zero and converts to numeric arrays.
It uses predict_proba column 1, otherwise sigmoid(decision_function), otherwise
clipped predictions. Class ordering and fallback meanings require verification.
A matching number/order of columns does not prove matching feature definitions;
zero filling can conceal missing Enhanced1 features. Horizon/target eligibility
metadata is not enforced by the inspected display path, which labels seven-day
risk. A 30-day bundle must not be presumed compatible with that display.

The UI shows rule/ML bands and per-tail scores, aggregates distinct tails by
command/band, and displays ML values as percentages. Missing/unusable model paths
can show rule-only results; exact error/fallback behavior must be evidenced from
the working reference, not generalized from damaged local code. No separate
NMCS-versus-NMCM classifier has been established.

## Unresolved acceptance evidence and change control

Before prediction implementation, reconcile the requested trainer spelling and
confirm the exact working intranet trainer/feature functions and artifact lineage.
Obtain approved sanitized input/output examples, ordered feature semantics,
class/target/horizon/eligibility metadata and runtime versions without publishing
artifacts or internal command categories. Preserve discrepancies until explicitly
resolved; alternative trainers are not automatically equivalent baselines.

Fictional parity cases must cover intra-day order, equal-time conflicts, partial
null records, weekends/missing days, late first observations, global versus
per-tail end dates, leading zeros, aliases/unknowns, current-assignment attribution,
NMCS-only reason summaries, persistent NMC-day counts, FIS-001 zero guards and
fleet/command/platform reconciliation. Prediction cases must cover window edges,
censoring, DEPOT/current-NMC eligibility, hours defaults, class ordering, feature
alignment and no future inputs. These are required future acceptance cases, not
newly implemented tests or claimed model evidence.

This contract freezes interpretation, not implementation authorization. Changes
require explicit customer approval and a recorded decision; never weaken FIS-001
regressions or FIS-002 deployment gates. Source/model access and real integration
retain separate approval boundaries.
