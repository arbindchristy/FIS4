# Phase 05B development-validation update - 2026-11-24

**Development completed; retain the empirical recovery baseline. No ML champion,
calibration, locked testing or promotion. Phase 05C remains NO-GO.**
Scientific dependencies are now runtime-qualified in the separate Windows Python
3.13.7 environment. Historical dependency-blocked preparation below is preserved;
its baseline measurements are not rewritten. No publication is authorized here.

## Experiment and temporal isolation

Existing branch feature/05b-nmcs-modeling, published HEAD
e087d3ebd1db1c60f3e9e736f7062241af2ccdaf / draft PR #16 unchanged. Reused the
verified six-year fictional artifact and existing TRAIN-only empirical parameter
JSON. No dataset generation or empirical-baseline refit. No legacy/untrusted model
was deserialized. Actual fitted pipelines were created in memory and dumped only
to ignored local evidence, never loaded from an untrusted file.

Dataset manifest SHA-256:
ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b.
Integrity hashing touches full file bytes; the loader filters timestamps before
constructing any Observation or accessing status/context fields after **2024-11-20**.
Only the development_replay section of prior baseline evidence is decoded, not its
full-period coverage/prevalence section. Calibration/test outcomes, prevalence and
performance were not inspected in this stage. Both remain RESERVED / NOT RUN.

| Role | Authorized window | Actual use |
|---|---|---|
| Training | 2020-11-21..2023-11-20 | Fit preprocessing and classifiers only |
| Development | 2023-11-21..2024-11-20 | Bounded configuration selection/comparison |
| Calibration | 2024-11-21..2025-11-20 | Reserved, not consumed or fitted |
| Locked test | 2025-11-21..2026-11-20 | Reserved, not consumed or scored |

Training reconstructs a fresh view at its outcome cutoff so later global endpoints
cannot extend training targets. Every sample audits T+H within its own partition.
No random row split or random internal early-stopping split. Development baselines
were replayed from frozen parameters solely to add required log loss/paired
uncertainty; every horizon Brier matches the published baseline to 1e-12.

Training references every 14 calendar days, 2020-11-21..2023-11-18. One seed-fixed,
label-blind offset from each available ten-day horizon bin. **208,800 examples,
7,412 NMCS positives**, outcomes through 2023-11-20. All offsets 1..180 occur (per-H
counts 1,000..1,334). Repeated tails, references and episodes are correlated; this
is not 208,800 independent aircraft failures. Sampling uses IDs only as RNG
metadata; tail identifiers are never model input.

Development uses the identical published weekly reference cohort, purged at H=180:
2023-11-21..2024-05-21, 27 dates x 160 tails = **4,320 examples per horizon**,
43,200 total across ten offsets, final target 2024-11-17. All methods use exactly
the same labels/metadata at each horizon, including current-NMCS aircraft. NMCM at
the target date is always negative. No onset/window-any-NMC relabeling.

## Features, preprocessing and predeclared candidates

The versioned nmcs-horizon-development-v1 schema layers the approved Phase 05A
history features with as-of history coverage/censor flags and known-horizon
log1p(H), current-NMCS x H and current-NMCS x log1p(H). No future state, receipt,
repair/closure, latent simulator cause or target-derived feature. Command/platform
are independent observed context, not organizational hierarchy or tail identity.

Training-only column selection drops inspection/phase because both are wholly
missing in this event projection; raw hours remain None/NaN. Nothing fabricates
hours. Other partial numeric missingness uses TRAIN medians plus missing indicators,
then TRAIN standardization. Current status/command/platform use TRAIN one-hot
categories with unknown categories ignored at transform. No validation fitting of
imputers/scalers/encoders; fitted statistics/categories are recorded. Six-year
history is requested/clipped, not falsely claimed complete for early examples.
Dataset-age features are not physical aircraft age and can cause extrapolation.

No oversampling or balanced class weights: preserve observed occupancy prevalence
for probability estimation. Rare-class diagnostics use AP/lift and current-status
groups; raw accuracy is not a selection metric. No calibrator is fitted.

Four configurations were fixed in pre_fit_plan.json before any model fit:

| ID | Algorithm | Explicit configuration |
|---|---|---|
| lr-c01 | L2 logistic | C=0.1, l1_ratio=0, lbfgs, tol=1e-6, max_iter=1000 |
| lr-c1 | L2 logistic | C=1, l1_ratio=0, lbfgs, tol=1e-6, max_iter=1000 |
| hgb-15 | Histogram gradient boosting | log_loss, learning_rate=.05, 150 iterations, 15 leaves, depth 4 |
| hgb-7 | Histogram gradient boosting | log_loss, learning_rate=.05, 150 iterations, 7 leaves, depth 3 |

All seed=42017, class_weight=None, one native thread. Both trees use
min_samples_leaf=200, L2=10, max_bins=127 and early_stopping=False. Logistic solvers
converged in 183/168 iterations without warnings. Trees completed their fixed
150-iteration budget; this is not proof of an optimal asymptotic solution.
All four passed finite [0,1] prediction checks for **every H=1..180**, separately
for current-NMCS and non-NMCS examples. Arbitrary offsets 14/45/123 are evaluated.

## Frozen selection rule and actual results

Primary: equal-horizon mean Brier, convergence required. Experimental practical
criterion: >=2% relative mean Brier improvement, no >5% per-horizon degradation,
and mean log loss no worse than the previously strongest empirical baseline.
These are predeclared research criteria, not customer-approved operational risk
thresholds or FIS-001 changes. Ties use log loss and deterministic ID order.
Current-status stability/interpretability and clustered uncertainty are disclosed.
No new configurations/features were tried after seeing the results.

| Method | Mean Brier | Mean log loss |
|---|---:|---:|
| historical_occupancy | 0.03076571 | 0.14103308 |
| persistence_recovery | 0.03042103 | 0.13846677 |
| transition_rule | 0.03051790 | 0.13881067 |
| hgb-15 | 0.03052928 | 0.13906575 |
| hgb-7 | 0.03050349 | 0.13894054 |
| lr-c01 | 0.03050050 | 0.13886260 |
| lr-c1 | 0.03046244 | 0.13869779 |

LR C=1 is the point-score best ML configuration, frozen in frozen_candidate.json
for reproducibility only. It is **0.1361% worse** in mean Brier than recovery and
worse in mean log loss. It improves Brier at only 7 and 180 of the ten tested
offsets. Practical improvement/reliability criteria fail; no ML champion selected.
The strongest baseline remains persistence_recovery. Neither a tiny advantage at
one horizon nor improved ranking overrides probability reliability and uncertainty.

Brier comparisons (all required checkpoints plus arbitrary offsets):

| H | Occupancy | Recovery | Transition | LR C=.1 | LR C=1 | HGB15 | HGB7 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0.028358 | 0.025164 | 0.025443 | 0.025277 | 0.024843 | 0.024700 | 0.024744 |
| 14 | 0.028573 | 0.028505 | 0.029089 | 0.028534 | 0.028570 | 0.028488 | 0.028476 |
| 30 | 0.029433 | 0.029394 | 0.029412 | 0.029494 | 0.029465 | 0.029528 | 0.029490 |
| 45 | 0.030723 | 0.030695 | 0.030699 | 0.030805 | 0.030781 | 0.030825 | 0.030791 |
| 60 | 0.030293 | 0.030256 | 0.030252 | 0.030390 | 0.030412 | 0.030360 | 0.030343 |
| 90 | 0.030078 | 0.030060 | 0.030060 | 0.030167 | 0.030193 | 0.030203 | 0.030165 |
| 120 | 0.029433 | 0.029395 | 0.029446 | 0.029577 | 0.029598 | 0.029765 | 0.029723 |
| 123 | 0.031798 | 0.031780 | 0.031806 | 0.031881 | 0.031894 | 0.032063 | 0.032052 |
| 150 | 0.033732 | 0.033730 | 0.033736 | 0.033778 | 0.033777 | 0.034006 | 0.033947 |
| 180 | 0.035237 | 0.035232 | 0.035236 | 0.035103 | 0.035093 | 0.035355 | 0.035304 |

Detailed best-ML development metrics (uncalibrated LR C=1):

| H | Log loss | ROC-AUC | AP | ECE10 | Top-decile lift | NMCS prevalence |
|---|---:|---:|---:|---:|---:|---:|
| 7 | 0.111940 | 0.7132 | 0.2184 | 0.008242 | 4.286 | 2.9167% |
| 14 | 0.131391 | 0.5980 | 0.0616 | 0.006757 | 1.496 | 2.9398% |
| 30 | 0.135644 | 0.5929 | 0.0389 | 0.008882 | 1.221 | 3.0324% |
| 45 | 0.140614 | 0.5847 | 0.0388 | 0.009463 | 1.241 | 3.1713% |
| 60 | 0.140011 | 0.5789 | 0.0421 | 0.010978 | 1.556 | 3.1250% |
| 90 | 0.139124 | 0.5850 | 0.0442 | 0.011580 | 1.343 | 3.1019% |
| 120 | 0.137361 | 0.5718 | 0.0341 | 0.011337 | 0.458 | 3.0324% |
| 123 | 0.145032 | 0.5742 | 0.0376 | 0.008653 | 0.634 | 3.2870% |
| 150 | 0.151324 | 0.5663 | 0.0391 | 0.005118 | 0.530 | 3.4954% |
| 180 | 0.154536 | 0.6008 | 0.0486 | 0.001624 | 1.266 | 3.6574% |

HGB15 has the best seven-day ML Brier (0.024700 vs recovery 0.025164), ROC-AUC
0.7357 and AP 0.2421, but its paired Brier interval includes zero and its mean
proper scores are worse overall. LR has better long-horizon ranking than recovery
at 180 days (AUC .6008 vs .5192), but the absolute Brier gain is only .000139,
with insufficient independent time clusters. Do not suppress these mixed findings
or describe them as operational accuracy or confirmed predictive superiority.

Log loss clips probabilities at 1e-15 consistently for all methods; Brier uses raw
probabilities. AP is tie-aware average precision, not trapezoidal PR integration.
ECE uses fixed ten bins; ranking ties use the existing 12-decimal convention.
Low ECE near rare prevalence does not certify individual calibration.

Expected fleet NMCS counts for LR versus recovery, same 160-tail cohorts:

| H | LR expected | Recovery expected | Observed | LR count MAE |
|---|---:|---:|---:|---:|
| 7 | 5.792 | 5.226 | 4.667 | 1.647 |
| 14 | 5.785 | 5.533 | 4.704 | 1.636 |
| 30 | 6.273 | 5.671 | 4.852 | 1.943 |
| 45 | 6.588 | 5.710 | 5.074 | 1.886 |
| 60 | 6.756 | 5.705 | 5.000 | 1.827 |
| 90 | 6.816 | 5.650 | 4.963 | 2.071 |
| 120 | 6.666 | 5.666 | 4.852 | 2.429 |
| 123 | 6.644 | 5.669 | 5.259 | 1.989 |
| 150 | 6.411 | 5.616 | 5.593 | 1.890 |
| 180 | 6.112 | 5.606 | 5.852 | 1.836 |

Current-status diagnostics for LR C=1 and recovery:

| H | Group | N/positive | LR Brier | Recovery Brier | LR log loss |
|---|---|---:|---:|---:|---:|
| 7 | NMCS | 123/44 | 0.216434 | 0.230536 | 0.621260 |
| 7 | other | 4197/82 | 0.019228 | 0.019146 | 0.097014 |
| 180 | NMCS | 123/5 | 0.038816 | 0.038998 | 0.170909 |
| 180 | other | 4197/153 | 0.034984 | 0.035122 | 0.154056 |

Only five positive outcomes exist in the current-NMCS H=180 group. Its ranking
metrics are explicitly unsupported/null, not evidence of safety. Complete subgroup
metrics and calibration coordinates for all seven methods/horizons are in the
local development_results.json. Supported LR command/platform variation:

| H | Dimension | Supported ranking groups | Brier range | AP range |
|---|---|---:|---:|---:|
| 7 | command | 4/4 | 0.012562..0.034114 | 0.0597..0.3248 |
| 7 | platform | 4/4 | 0.018062..0.028538 | 0.1996..0.2749 |
| 180 | command | 4/4 | 0.017291..0.053295 | 0.0317..0.0673 |
| 180 | platform | 4/4 | 0.027709..0.038149 | 0.0475..0.0926 |

## Dependence, interpretation and failure modes

Paired bootstrap compares losses on identical rows, with resampled aircraft and
reference-time blocks of max(28,H) days, 200 replicates, seed 42017. At least five
time blocks are required; otherwise intervals are explicitly unavailable. These
are nominal post-selection development diagnostics, not independent confirmation
or multiple-comparison-adjusted superiority claims.

| H | LR minus recovery Brier | Time blocks | Paired interval/status |
|---|---:|---:|---|
| 7 | -0.000321 | 7 | [-0.001056, 0.000115] |
| 14 | 0.000065 | 7 | [-0.000720, 0.000512] |
| 30 | 0.000071 | 7 | [-0.000399, 0.000421] |
| 45 | 0.000086 | 5 | [-0.000267, 0.000361] |
| 60 | 0.000156 | 4 | Unsupported: <5 time clusters |
| 90 | 0.000133 | 3 | Unsupported: <5 time clusters |
| 120 | 0.000203 | 2 | Unsupported: <5 time clusters |
| 123 | 0.000114 | 2 | Unsupported: <5 time clusters |
| 150 | 0.000047 | 2 | Unsupported: <5 time clusters |
| 180 | -0.000139 | 2 | Unsupported: <5 time clusters |

The seven-day LR interval [-.001056, .000115] and HGB15 interval
[-.001526, .000312] both include zero. At H=180 there are only two time blocks;
no defensible paired interval is reported. Weekly references, repeated episodes,
and common horizon outcomes remain correlated. The raw row count is not an
independent sample-size claim. Independent seeds/tails and final locked testing
remain necessary; none was substituted for the reserved test here.

LR standardized-numeric/one-hot coefficients: current NMCS +5.9889,
NMCS x log(H+1) -1.6816, current DEPOT -1.3680, fictional command D -0.8709,
command B +0.5625. These are conditional associations in a collinear regularized
encoding, not causal effects or simple standalone odds ratios. Full top coefficients
are recorded for both LR candidates.

Bounded grouped permutation: 1,600 DEVELOPMENT rows, three repeats per group.
HGB15 mean Brier increase: command +.000547, NMCS history +.000162, horizon
+.000141; platform -.000080 and state age -.000025. Negative values and variance
across repeats indicate noise/correlation/instability, not causal irrelevance.
Derived horizon interactions are recomputed consistently after permutation. No
feature elimination or extra tuning followed these post-fit explanations.

Limitations: one fictional stationary world; artificial command profiles and
platform allocations; current assignments rather than historical transfers; left-
truncated early history; no inspection/phase features; dataset age is not aircraft
age; training priors and validation prevalence differ; sparse current-NMCS subgroup;
long-horizon dependence. Do not infer operational performance from these results.

## Artifacts, actual execution and verification

Local ignored evidence: .harness-test-tmp/phase05b-ml-development-v2/.
The pre-fit plan fixes sampling, configs and criteria with source/runtime/data
hashes before fitting. Manifest lists hashes of four newly fitted pipeline joblibs,
plan, prediction CSV, metrics and frozen provisional configuration. Models are
NOT promoted and are not included in Git. Future loads require trusted provenance
and manifest verification; no general untrusted loader was introduced.

Development manifest SHA-256: `689b0f5e8a5d5bc100f090bb5820125a83c0fdcda10d4b0ee4b8990ee368c938`.

- hgb-15.joblib: `a0f86f166b1f6d2f10de881dc0a0aac9034c6494463a239af1cfbc490765cfd9`
- hgb-7.joblib: `b5720b5649329e346876591a2030a76a01d978b87e2f877ffdae62837b16f111`
- lr-c01.joblib: `a2319c8075b148fb03c6973816089a50b8f5740482affac71b655bfd1bbe8746`
- lr-c1.joblib: `6d95dc923cfda7224602faeafa68a0a7e6962a29bae0315158c907d4b1060453`

Source revision e087d3e plus exact working-source hashes is recorded; new training
code is not falsely claimed to exist in that published revision. Runtime remains
Python 3.13.7, sklearn 1.9.1, SciPy 1.18.1, NumPy 2.3.4, pandas 2.3.3,
joblib 1.6.0, threadpoolctl 3.8.0 and the previously qualified supporting pins.
No new downloads/installations. The application .venv and production pins remain
unchanged; this is Windows development evidence, not Linux or offline-package
acceptance. Later inference packaging/memory/cold-start gates remain required.

Actual command:

```powershell
.harness-test-tmp/phase05b-ml-env/Scripts/python.exe -B scripts/train_nmcs_development.py --experiment phase05b-ml-development-v2
```

Exit 0; 53.258 s feature preparation, 120.386 s total recorded run. Four fixed
candidate fits completed; LR 168/183 iterations, trees fixed 150. No uncontrolled
search. An initial v1 attempt was stopped after preparation when a misplaced
pandas import was noticed; no model results from it were selected or reused. Its
plan/log/status are preserved. The import-only correction did not alter candidate
settings, sampler, criteria or data. No dataset was regenerated.

Focused isolated suite: 14/14 PASS, 4.068 s. It proves cutoff isolation including
future-global-end truncation, horizon/label alignment, missingness/encoding guards,
current-NMCS/NMCM targets, deterministic tiny-fixture fits, probability/schema
validity and refusal to construct calibration/test batches. Full-size training
was not repeated to manufacture bit-for-bit evidence; exact source/seed/configs,
artifacts and deterministic fixture checks are recorded. Native cross-platform
bitwise reproducibility is not claimed.

Existing foundation 41/41 PASS (0.777 s); protected readiness 28/28 PASS (1.067 s).
Application portable: 229 tests, 0 failures/errors, **8 new isolated-estimator-only
skips** (128.734 s): 221 passed. All eight skipped tests executed successfully in
the isolated 14-test suite. Original 215 portable tests remain passing; five
external-reference cases remain separate. Commands/security disposition and exact
file inventory are recorded in PROJECT_STATE.md. No frontend/build suites rerun.

**Recommendation:** retain persistence_recovery; no ML champion or promotion.
Do not proceed automatically to calibration as if ML superiority were established.
If the chief architect separately authorizes diagnostic calibration research,
freeze lr-c1 exactly as recorded and compare calibrated probabilities with the
unchanged baseline; do not tune on or inspect the locked test. This is a research
option, not a GO decision. Phase 05C remains NO-GO. No calibration, locked test,
commit, push, PR #16 modification, merge or deployment occurred in this task.

---

## Phase 05B final scientific protocol v1.1

Chief-architect calibration gate on draft PR #16. Phase 05C remains
NO-GO. Authorization covers calibration only. The locked period remains sealed. Use the published development
results and the fictional six-year dataset already on disk.

### Frozen methods and endpoint

Primary forecast: unmodified persistence_recovery. Sole ML comparator: frozen
lr-c1. Historical occupancy and the transition rule remain fixed empirical
references. Historical occupancy is the sole confirmatory benchmark.
No reselection, base-model fitting, or preprocessing updates. Predict NMCS
occupancy exactly T+H, H=7/30 primary; H=14/45/60/90/120/123/150/180 secondary.
Current NMCS is eligible. Valid NMCM targets are negative. Report all registered
horizons; no implication for unscored offsets.

### Decision thresholds

Apply these proposed margins as written after approval and before outcome access.
Loss deltas are forecast minus reference on identical eligible rows. All
locked acceptance and harm Brier/log-loss margins (including subgroup Brier)
compare raw recovery against frozen historical occupancy in the same horizon
and subgroup. Bias and ECE compare each forecast to observed rates in that
cohort. Transition and ML contrasts report recovery or the named comparator
explicitly and have no acceptance margins. Use unclipped probabilities for Brier
and clip to [1e-15, 1-1e-15] for natural-log loss only.

| Gate | Numerical rule |
|---|---|
| Material Brier skill | Recovery Brier at least 2% lower than occupancy; one-sided paired 97.5% upper bound on recovery-minus-occupancy Brier strictly below zero |
| Log-loss guard | Recovery-minus-occupancy log loss <= 0.002 nats per example |
| Overall reliability | Absolute mean probability minus prevalence <= 0.010 and ten-bin equal-width ECE <= 0.015 |
| Subgroup guard | For each required supported subgroup, absolute mean probability minus prevalence <= 0.030 and recovery-minus-occupancy Brier <= 0.005 |
| Overall support | >=1,000 rows, >=50 positives and >=50 negatives, >=100 distinct tails and >=20 reference dates per horizon |
| Subgroup support | >=100 rows, >=20 positives and >=20 negatives, >=20 distinct tails and >=10 reference dates per horizon |
| Material overall harm | Recovery Brier at least 5% above occupancy, log-loss excess >0.010, absolute mean bias >0.030, or ECE >0.040 on a supported primary horizon |

Required subgroups are current NMCS versus other, each command, and each
platform in the frozen fictional roster. Report denominators and exclusion
counts. Below support, retain descriptive counts and mark subgroup ranking,
reliability and acceptance as unsupported. Use the existing twelve-decimal
ranking tie convention. Report ROC-AUC, average precision, prevalence, top-decile
lift and expected/observed NMCS counts and count MAE by reference date. Use bins
[0,.1), [.1,.2), ..., [.9,1], counting empty bins as zero weight. Report counts
and mean predicted/observed rates per bin; bins with fewer than 50 rows or five
positives are descriptive only. Ranking is descriptive and cannot override a
proper-score or reliability failure.

Two one-sided primary Brier claims form one family, each tested at alpha .025
(Bonferroni family alpha .05). Report both regardless of support. An unsupported
claim does not recycle alpha. Secondary horizons, ML contrasts and subgroup
diagnostics are descriptive and cannot qualify a horizon. The 2% and guard
margins are point-estimate gates in addition to the Brier uncertainty gate.

### Optional comparator calibration

Recovery stays raw. Authorize only one diagnostic recalibration of lr-c1.
Fit one shared sigmoid p'=sigmoid(a+b*logit(clip(p,1e-6,1-1e-6))) with an
intercept, unweighted Bernoulli log loss and no tuning. Require a finite,
converged fit with strictly positive slope; reject separation or fit failure.
Pool the 7- and 30-day cohorts with equal total weight per horizon for fitting
and evaluation. Apply any accepted mapping only to 7 and 30 days. All secondary
comparator forecasts remain raw. Always report raw lr-c1 alongside any accepted
variant.

Anchor weekly dates on 2024-11-21. Use expanding fits from that date with these
inclusive fit-outcome cutoffs and assessment reference windows:

| Fit outcome cutoff | Assessment references |
|---|---|
| 2025-02-28 | 2025-03-01 through 2025-04-30 |
| 2025-04-30 | 2025-05-01 through 2025-07-31 |
| 2025-07-31 | 2025-08-01 through 2025-11-20 |

For each fit, require both primary outcomes by its cutoff; for each assessment,
require both by the end of its window. Use common tails/dates across the two
offsets, following the eligibility rules below. Require per horizon per fit
>=500 rows and >=25 outcomes of each class. Require per horizon per assessment
>=300 rows and >=10 of each class, and >=5 reference dates. Any unsupported fold
or invalid output defaults to raw lr-c1; no combining folds or changing windows.
Before any sigmoid fit, every assessment fold must support at least six
nonoverlapping 30-day reference blocks with at least three eligible dates each,
and at least five of those blocks must contain both classes at each primary
horizon. Anchor blocks at the assessment window start. These counts are minimum
proxies for independent time support. Failure of even the calendar upper bound
precludes fitting. Assess raw recovery over the full eligible calibration period
using the common 30-day purge, with no acceptance claim from calibration metrics.
On concatenated out-of-fold predictions require equal-horizon mean log loss at
least 1% lower than raw, Brier excess <=0.0002 and ECE excess <=0.002 at each
primary horizon, and pooled mean log-loss excess versus raw lr-c1 <= 0.000000000001 nats per
example in each individual fold (floating-point tolerance only). Every
calibration improvement or excess above compares calibrated with raw lr-c1 on
the identical rows. The Brier and ECE excesses are absolute differences.
If all pass, refit the same two coefficients once using all eligible
calibration references/outcomes through 2025-11-20 (same fit support minimum).
Seal coefficients, fit diagnostics and the raw/calibrated choice before test
access. A failed final fit defaults to raw. Calibration findings do not change
the primary forecast or selection.

### Single locked replay

Anchor a seven-calendar-day reference grid on 2025-11-21 and retain dates
through 2026-11-20 minus 180 days, inclusive. Use the frozen synthetic projection
and Phase 05A reference eligibility and validated reconstruction at the
relevant outcome cutoff. Preserve leading zeros. Build features from history
through the reference day only, including permitted earlier-period history.
Require a valid exact-date target at all ten offsets for each eligible tail and
reference. Unavailable or unvalidated targets are missing; never encode them as
negative. Apply the equivalent common-target rule for the two calibration
offsets. Sort by reference date, tail and horizon. Record counts by horizon and
group and mutually exclusive exclusions in this order: calendar purge,
ineligible reference, missing/unvalidated target. Source corruption, duplicate
cohort keys, invalid predictions, or method row mismatches stop the run;
method-specific row removal is forbidden. Check leakage and cohort equality
before scoring. Save hashed cohort keys, predictions, exclusions, results and
execution log locally. Run all registered metrics in one authorized execution,
with no outcome-informed retries, thresholds, subgroup pooling or corrections.
An aborted run after outcome access consumes the blind holdout for any
outcome-informed repair; obtain a new independent holdout in that case.

### Paired uncertainty and decisions

For each contrast and horizon compute paired row loss differences. Use
nonoverlapping calendar blocks of max(28,H) days anchored at the first locked
reference. Independently resample the distinct aircraft and nonempty blocks
with replacement, drawing the original number from each dimension. Weight
each observed row by the product of its aircraft and block multiplicities.
Compute weighted mean deltas for Brier and log loss. Use 10,000 draws, Python
random.Random seed 42017 reset per horizon and contrast, sorted sampling keys,
identical draws for both losses, and linear-interpolated percentile bounds.
Skip zero-weight draws. Report two-sided 95% descriptive intervals and the
97.5th-percentile upper Brier bound for the primary gate. Suppress intervals
unless overall support passes, >=6 blocks each contain >=3 reference dates,
>=5 of those qualifying blocks contain at least one positive and one negative,
and >=9,500 draws
have nonzero weight. Resampling accounts for crossed dependence approximately;
it cannot substitute for independent fleets or calendar periods. If any support
condition fails, the interval is unavailable and the horizon cannot earn PASS.

- **Fictional limited-horizon PASS** requires at least one supported primary
  horizon to pass every skill, uncertainty, reliability and subgroup gate and
  no material overall harm on either supported primary horizon. Name only
  qualifying horizons. A missing required subgroup blocks PASS for its horizon.
- **Exploratory only** applies if neither primary horizon qualifies and there
  is a >=2% Brier point gain on a primary horizon meeting overall support, with
  no material overall harm, but at least one acceptance gate fails.
- **NO-GO** applies for integrity/leakage failures, material overall harm on
  either supported primary horizon, or absence of even the exploratory evidence.
  No decision promotes lr-c1 or changes the Phase 05C gate.

### Freeze and access checklist

1. Obtain approval of this protocol and separate explicit authorization for
   reserved access. Log operators, inputs, partitions and allowed actions.
2. Record SHA-256 for this approved text, exact evaluation source, its tests,
   frozen feature/cohort sources, dependency/runtime lock, dataset and empirical
   artifacts and lr-c1 artifact. Bind these to a reviewed Git revision and the
   published development manifest (689b0f5e8a5d5bc100f090bb5820125a83c0fdcda10d4b0ee4b8990ee368c938)
   and dataset manifest (ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b).
   Hashes must match trusted manifests. Audit provenance before any separately
   authorized model load. Never load legacy models. Dry-run evaluator and failure
   cases with small fabricated fixtures only; the existing development runner
   deliberately rejects reserved partitions.
3. First reserved access includes parsing calibration statuses as covariates or
   labels, reconstructing snapshots, determining eligibility/exclusions/support,
   generating probabilities from those covariates, fitting sigmoid coefficients
   and inspecting assessment metrics or intermediate rows. Authorize and log
   these together. Restrict the loader to the calibration cutoff. Keep raw
   records, intermediate output and model artifacts local. Do not open older
   full-world coverage reports, which may expose reserved outcome summaries.
4. Seal and hash the calibration decision, coefficients if any, ordered input
   schema, evaluator and report format. Independently verify freezes before
   authorizing the single test run. First locked access includes parsing locked
   statuses even for features, reconstruction, eligibility/support counting,
   target extraction, scoring and inspecting outputs. Release results together
   after the run. Log any exposure, failure or deviation and suspend acceptance
   until independently reviewed.

The common 180-day purge leaves 27 scheduled locked references before eligibility
checks. Long horizons cannot meet the interval rule within that calendar.
Rare positives may also block subgroup or fold support. Overlapping
outcomes, repeated tails and one fictional world limit generalization. Missing
inspection and phase hours and limited historical depth constrain transfer.
Operational release still requires approved intranet source mappings, validated
as-of availability and reconstruction, representative real coverage, independent
temporal reliability and subgroup validation, customer-approved operating
thresholds, and Linux/Windows offline runtime, memory and release acceptance.

---

## Historical preparation checkpoint (dependency status superseded)

The previous report follows unchanged for historical evidence. Its package-blocker
status is superseded by runtime qualification and this development update. Its
full-world descriptive preparation statistics were not decoded by ML training or
used for selection; calibration/locked outcomes remain reserved in this stage.

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
