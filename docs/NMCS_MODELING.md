# Phase 05B preparation and empirical development report

Recorded 2026-11-24 (Asia/Dubai). **PARTIAL / DEPENDENCY BLOCKED; NO-GO for Phase 05C.**
No ML candidate or probability calibrator has been fitted; the locked out-of-time
period has not been evaluated. These are empirical baseline development results,
not completed scientific validation or operational prediction acceptance.

## Baseline, isolation and dependency gate

Branch feature/05b-nmcs-modeling at required merged PR #15 baseline
cb12229071dcae580d636300b9119aaf4f5a1a48. Existing unrelated untracked patches,
launcher, worktrees and historical evidence are preserved. FIS-001/FIS-002/FIS-003,
Phase 05A feature/label behavior, readiness, APIs, simulator, React, SQL and Render
files/dependencies remain unchanged. No legacy model was opened or deserialized.

Existing environment: CPython 3.13.7 Windows x64, NumPy 2.3.4, pandas 2.3.3.
scikit-learn, SciPy, joblib and threadpoolctl are **not installed**; no separate
workspace modeling environment or local scientific wheel bundle was found.
No package was downloaded, installed or upgraded. Per the customer fallback,
only dependency-independent preparation, empirical baselines and tests proceeded.
Regularized logistic regression and gradient-boosted classifier implementation,
training, tuning and evaluation are blocked, not substituted with homemade ML.
Their numerical hyperparameters and native wheels are not approved or verified.

To unblock: separately approve a pinned scientific environment or audited offline
wheel bundle, isolated from .venv. Verify CPython/NumPy/scikit-learn/SciPy/joblib/
threadpoolctl compatibility and native Windows x64 and Linux x64 wheels/imports.
No exact new version compatibility or Linux execution is claimed. HistGradient-
Boosting is a possible scikit-learn candidate, not an installed/tested selection;
a separate XGBoost dependency is not required by this preparation.

## Separate fictional dataset and observed-only projection

Existing supported SimulationConfig(as_of=2026-11-20, seed=42017, years=6), 160 tails.
Generated interval **2020-11-21..2026-11-20**, 2,191 days / **350,560 aircraft-days**.
Four fictional commands, 40 tails each; UH-60L/UH-60M/AH-64E/AW139, 40 each.
This is a different deterministic world, not an extension of the four-year dashboard
history. The simulator algorithm/default and dashboard cache were not changed.

Only normalized status-change/boundary events with date/tail/status/command/platform
enter this experiment. The approved carry-validation policy is explicit. No fault
cause, future receipt, sampled repair duration, closure or latent episode state is
read by preparation/fitting. Source assessment derives runs from daily statuses.
Inspection and phase hours both remain None in this event-only projection. Existing
operations could supply observable inspection in a later reviewed adapter; phase
is absent and cannot be fabricated. No real source/assignment acceptance is implied.

Actual assessment:
- NMCS days 12,950 / 350,560 = **3.694089%**.
- **1,361 separate NMCS runs**, zero initially left-censored; seven ongoing at cutoff.
- 1,354 completed durations: mean 9.5325, median 9, range 2..24 days; p10/p90 3/17.
- 1,202 start-to-start recurrence intervals: mean 228.764, median 155.5, range
  4..1,663 days; p10/p90 35/512. Episodes/labels are not IID failures.
- 350,400 reference-eligible tail-days (one fleet-wide reference-gap day excluded).
- Complete rolling 30/90/180/365-day features: 345,760 / 336,160 / 321,760 / 292,320
  reference-tail pairs respectively. Missing hours: 100% in this projection.
- All 180 horizon eligibility/positive counts are in the versioned development JSON.

| H | Eligible labels | NMCS positives |
|---|---:|---:|
| 1 | 350,240 | 12,947 |
| 7 | 349,280 | 12,918 |
| 30 | 345,600 | 12,810 |
| 60 | 340,800 | 12,652 |
| 90 | 336,000 | 12,417 |
| 120 | 331,200 | 12,200 |
| 150 | 326,400 | 12,006 |
| 180 | 321,600 | 11,843 |

A six-year world does not give six years of prior data to early training references.
At most the final day has a complete six-year lookback, with no within-dataset
future outcome. Do not require full six-year feature history and simultaneously
claim these labeled training examples have it. Existing clipped-history/coverage
semantics remain explicit. More warm-up history requires a separately approved
experimental design within the unchanged simulator's supported bounds.

## Chronological design and leakage control

| Partition | Dates | Use in this run |
|---|---|---|
| Training | 2020-11-21..2023-11-20 | Empirical counts only |
| Validation | 2023-11-21..2024-11-20 | Development baseline replay |
| Calibration | 2024-11-21..2025-11-20 | Reserved; no calibrator fitted |
| Locked test | 2025-11-21..2026-11-20 | Reserved; no forecasts scored or model selected |

Every permitted example requires reference >= partition start and T+H <= partition
end/validated-data cutoff. Training uses a fresh cutoff reconstruction, so future
outcomes/global endpoints do not affect fitted parameters. An empty partition or
unsupported reference fails explicitly. No random aircraft-day split or global
preprocessor fitting occurs. Fixed raw schema keeps numeric None values and text
command/platform/status context; tail is sample metadata, never a numeric feature.
No encoder, imputer, scaler or probability calibrator is implemented/fitted yet.

Replay uses a predeclared common cohort across all ten evaluated horizons:
7/30/60/90/120/150/180 plus arbitrary offsets 14/45/123. Weekly reference dates
2023-11-21..2024-05-21, 27 dates x 160 tails = **4,320 examples per horizon/method**.
Using the 180-day purge makes the methods and horizon comparisons use identical
reference populations. All targets stay inside validation. Predictions use only
frozen training parameters and the current as-of state. Current-NMCS tails remain
eligible. No ML model selection or locked-test comparison has happened.

## Empirical baselines and explanations

1. Historical occupancy: training usable NMCS days / training usable aircraft-days.
2. Persistence/recovery: empirical P(NMCS at T+H | current canonical status),
   separately estimated for all H=1..180 from training labels. Empty cohorts back
   off explicitly to training occupancy, with support/fallback in the explanation.
3. Transition rule: six-state empirical one-day transition matrix advanced H times;
   empty transition rows use the observed training state distribution. This is a
   time-homogeneous first-order assumption, not arbitrary Streamlit risk weights.

All emit the same probability/horizon/target-date/explanation contract. Explanations
include training cutoffs, positive/usable day counts, conditional cohort support
and transition counts. These are historical associations, not established causes.
The baseline JSON stores empirical parameters, schema and assumptions, with no
pickle/joblib or executable estimator. Inference needs no network or training.

## Actual development results (not locked-test or ML performance)

Brier is the primary development loss, not raw accuracy. PR-AUC is explicitly
tied-score **average precision**, not trapezoidal PR integration. Rank/lift diagnostics
round probabilities to 12 decimal places so machine-epsilon differences cannot
create apparent ranking skill; Brier/calibration use unrounded probabilities.
Top-decile ties receive fractional allocation (minimum cohort size one).

| H | Occupancy Brier | Recovery Brier | Transition Brier | Recovery ROC-AUC | Recovery AP | NMCS prevalence |
|---|---:|---:|---:|---:|---:|---:|
| 7 | 0.028358 | 0.025164 | 0.025443 | 0.6897 | 0.1461 | 2.9167% |
| 14 | 0.028573 | 0.028505 | 0.029089 | 0.5516 | 0.0345 | 2.9398% |
| 30 | 0.029433 | 0.029394 | 0.029412 | 0.5346 | 0.0340 | 3.0324% |
| 45 | 0.030723 | 0.030695 | 0.030699 | 0.5230 | 0.0335 | 3.1713% |
| 60 | 0.030293 | 0.030256 | 0.030252 | 0.5338 | 0.0335 | 3.1250% |
| 90 | 0.030078 | 0.030060 | 0.030060 | 0.5218 | 0.0324 | 3.1019% |
| 120 | 0.029433 | 0.029395 | 0.029446 | 0.5582 | 0.0364 | 3.0324% |
| 123 | 0.031798 | 0.031780 | 0.031806 | 0.5293 | 0.0359 | 3.2870% |
| 150 | 0.033732 | 0.033730 | 0.033736 | 0.5232 | 0.0369 | 3.4954% |
| 180 | 0.035237 | 0.035232 | 0.035236 | 0.5192 | 0.0378 | 3.6574% |

Short-horizon recovery information has useful development separation. At 180 days,
recovery Brier improves on constant occupancy by only about **0.0000053**; AUC is
about 0.519 and AP 0.0378 versus prevalence 0.0366. This is not credible evidence
of material long-horizon value or of an ML improvement. No positive release claim
is made from these differences. No full Phase 05B model is recommended yet.

Selected diagnostics (all methods/horizons, calibration coordinates and subgroup
results are retained in development_report.json):

| H | Method | ECE (10 bins) | Top-decile lift | Mean expected fleet NMCS | Mean observed | Fleet count MAE |
|---|---|---:|---:|---:|---:|---:|
| 7 | historical_occupancy | 0.006478 | 1.000 | 5.703 | 4.667 | 1.679 |
| 7 | persistence_recovery | 0.003495 | 4.010 | 5.226 | 4.667 | 1.505 |
| 7 | transition_rule | 0.003039 | 4.010 | 5.153 | 4.667 | 1.492 |
| 180 | historical_occupancy | 0.000929 | 1.000 | 5.703 | 5.852 | 1.863 |
| 180 | persistence_recovery | 0.001536 | 1.128 | 5.606 | 5.852 | 1.862 |
| 180 | transition_rule | 0.000866 | 1.146 | 5.713 | 5.852 | 1.862 |

Calibration curve coordinates for recovery (nonempty fixed bins):

| H | Bin | N | Mean predicted | Observed frequency |
|---|---:|---:|---:|---:|
| 7 | 0 | 4197 | 0.022318 | 0.019538 |
| 7 | 3 | 123 | 0.385618 | 0.357724 |
| 180 | 0 | 4320 | 0.035038 | 0.036574 |

Low ECE at rare prevalence is not proof of individualized calibrated risk. No
probability calibration model has been fitted. Current NMCS versus not-NMCS:

| H | Group | N / positives | Recovery Brier |
|---|---|---:|---:|
| 7 | Not NMCS | 4197 / 82 | 0.019146 |
| 7 | Already NMCS | 123 / 44 | 0.230536 |
| 180 | Not NMCS | 4197 / 153 | 0.035122 |
| 180 | Already NMCS | 123 / 5 | 0.038998 |

The already-NMCS H=180 subgroup has only five positives; ranking/calibration
interpretation there is underpowered. Command/platform descriptive metrics are
reported only for n>=100 with >=10 positives and negatives; otherwise marked
insufficient support. Group variation is not evidence of causal organizational
or platform effects. No hidden battalion or real organization fields are present.

Descriptive recovery-baseline group variation (supported groups only):

| H | Dimension | Supported groups | Brier range | AP range |
|---|---|---:|---:|---:|
| 7 | command | 4/4 | 0.013495..0.033989 | 0.0318..0.2413 |
| 7 | platform | 4/4 | 0.018015..0.029626 | 0.1270..0.1698 |
| 180 | command | 4/4 | 0.017587..0.053762 | 0.0174..0.0578 |
| 180 | platform | 4/4 | 0.027893..0.038253 | 0.0368..0.0419 |

Exploratory two-way pigeonhole bootstrap: tail clusters and 28-day reference blocks,
200 replicates, seed 42017. There are 160 tail clusters but only **seven time blocks**.
Recovery Brier marginal 95% percentile intervals: H=7 [0.017616, 0.034790]; H=180
[0.026251, 0.042742]. These are not paired skill intervals or deployment evidence.
Weekly references and overlapping 180-day outcomes remain dependent; 28-day blocks
do not remove long-horizon dependence. More independent periods/seeds and a paired
block/cluster comparison are needed. No statistical superiority is asserted.

## Artifacts, provenance and reproducibility

All artifacts remain ignored locally under
`.harness-test-tmp/phase05b-six-year-42017-v3/`:
observations.csv, baselines.json, development_report.json and manifest.json.
They are wholly fictional; **ml_artifact is null**. No model artifact is included
in Git/public deployment. Manifest format fis4-modeling-preparation-v1 records
feature schema/order, algorithm assumptions, partition dates, evaluation ID, seed,
Python/package versions, source revision plus exact working-source SHA-256 hashes,
and integrity hashes for every data/baseline/report file. Source revision is the
merged baseline, not a false claim that the uncommitted preparation existed there.
Hashes detect changes against a trusted manifest; they are not signatures/authentication.

Final manifest SHA-256: `ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b`.

- baselines.json: `85b1d51fe7de78b617cef2770835555e85405428906f5f1b5b827b002ee86ca9`
- development_report.json: `879d919da874da580fb6743e03a1d986be4c63a8527831c2b7558e73854b006a`
- observations.csv: `40c96adc8984c597ba8cd108abae63d708d8030edf682cff904b5f7f23913969`

Actual commands from repository root (existing .venv, no installation):

```powershell
.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py
.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py --reuse-dataset phase05b-six-year-42017-v1 --output-name phase05b-six-year-42017-v2
.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py --reuse-dataset phase05b-six-year-42017-v2 --output-name phase05b-six-year-42017-v3
```

Initial generation/preparation took 47.640 s. v2 (22.601 s) added conservative
ranking precision after a numerical counterexample; v3 (26.152 s) completed rolling
feature-availability metadata. Both reuse the verified original CSV, not regeneration.
All three original artifacts/logs remain; equal data/baseline hashes are verified.
Dataset reuse checks manifest integrity, configuration and frozen generator hashes;
existing experiment directories cannot be overwritten. No performance/memory or
Windows/Linux inference benchmark is implied by these laptop elapsed times.

## Windows offline and remaining acceptance

Pure baseline preparation/inference parameters need standard-library Python; the
assessment reuses current pandas/NumPy. No change to Windows app pins or Linux
Render lock. Actual Linux scientific/runtime compatibility remains untested.
Future ML needs an approved separate scientific environment, exact wheel/native
inventory, schema/estimator integrity, reproducible fitting and independent
out-of-time evaluation before choosing an artifact. No LLM/cloud services required.
FIS-002 still requires bundled Windows x64 runtime/dependencies/native libraries,
verified artifacts and clean isolated exact-package tests; no destination pip,
internet or training. Later Render ML integration needs separate Linux memory,
cold-start and functional acceptance. This preparation changes no running service.

**NO-GO for Phase 05C**: logistic/boosted candidates, train-only preprocessing,
calibration, independent locked testing, paired uncertainty of improvement and
artifact runtime validation are NOT RUN. A baseline development result cannot
satisfy the rule that an ML model beat the strongest simple baseline. Per the
explicit dependency fallback, affected experiments stopped rather than installing
packages or fabricating results. Full Phase 05B scientific acceptance remains blocked. Only this clearly marked
preparation may be published for review after code/security checks pass; such a
PR does not certify ML completion. No merge or deployment is authorized.
Verification commands/results and source inventory are recorded in PROJECT_STATE.md.
