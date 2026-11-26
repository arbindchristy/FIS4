# FIS4 project state

## Phase 05B locked evaluator preparation (protocol v1.1)

Seven fixture and seal checks passed in the qualified scientific environment.
The protocol and calibration source/artifacts still match their recorded hashes.
No locked observations were opened or hashed, and no authorization marker or
execution directory was created. Phase 05C remains NO-GO.

Proposed one-time command, from the repository root after separate approval:

```powershell
.harness-test-tmp/phase05b-ml-env/Scripts/python.exe -B scripts/evaluate_nmcs_locked.py --freeze-sha256 d002f9890da2a1c04d3e20bd78ee1d3ff76efb1af5484600224316b8b71b7323 --authorization-marker .harness-test-tmp/phase05b-locked-v1.1-authorization.json
```

The marker is a local review interlock. Only after explicit chief-architect
approval, create the JSON file at that path with these fields:

```json
{
  "authorization": "AUTHORIZE_ONE_TIME_PHASE05B_LOCKED_TEST_V1_1",
  "freeze_sha256": "d002f9890da2a1c04d3e20bd78ee1d3ff76efb1af5484600224316b8b71b7323",
  "period": ["2025-11-21", "2026-11-20"],
  "approval_reference": "<actual approval record and operator>"
}
```

Confirm reviewed file hashes against the local freeze manifest. The evaluator
records authorization and creates an exclusive output directory before reading
the export. Keep the directory, including a failed attempt, as the replay
interlock and audit record. Do not retry after outcome exposure. On success the
directory contains the machine report, cohort keys, predictions and their hashes.
Unsupported primary horizons are inconclusive and cannot earn PASS. An authorized
replay could still fail its support or skill gates. Real-data intranet acceptance
remains separate.


## Phase 05B calibration gate (protocol v1.1)

Calibration-only replay completed in the qualified Python 3.13.7 scientific
environment on feature/05b-nmcs-modeling, based on b3a4419. Raw recovery remains
primary and raw lr-c1 remains the sole comparator. No sigmoid was fit. The
three forward assessment folds had 1, 2, and 3 qualifying mixed time blocks at
each horizon, below the required six qualifying blocks and five mixed blocks.
The first fold also had just four reference dates, below the required five.

Common full calibration cohort: 7,680 examples per horizon, 160 tails and 48
reference dates; 800 tail/date pairs purged, zero ineligible or missing. Raw
recovery at H=7/30 respectively: Brier 0.033657/0.036416, log loss
0.139669/0.160576, signed bias -0.003220/-0.002118, ECE 0.003220/0.002118.
These are fictional calibration-period diagnostics. Locked outcomes remain sealed.

Local evidence is under .harness-test-tmp/phase05b-calibration-v1.1.
Pre-access freeze SHA-256: f8b1274636fe599f7f56057586f6fd9a23ef99c30bc8d82432b097d23739851d.
Result SHA-256: 8d684bfe868b36c0c6c70d1e425a78060bbed59ccac37960b88dcef9fe273344.
Seal SHA-256: 595c5c3bd4ad95dc33cc3e729b37b509ae2da6c6244397ac6ff66fe963ac01a3.
The in-scope observation prefix agreed across two saved exports. The original
whole-export hash was reused as historical evidence; it was not recomputed
because the export spans the sealed period. No model deserialization.
Three fabricated-fixture gate tests passed in the isolated environment.


## Phase 05B ML development validation - 2026-11-24

Authorized training/development only, on feature/05b-nmcs-modeling, HEAD e087d3e;
draft PR #16 is unchanged. No commit, push, staging, PR modification, merge or
deployment. Scientific environment .harness-test-tmp/phase05b-ml-env is qualified:
Python 3.13.7 / sklearn 1.9.1 / SciPy 1.18.1 / NumPy 2.3.4 / pandas 2.3.3 /
joblib 1.6.0 / threadpoolctl 3.8.0, approved support pins unchanged. No installs.
The earlier dependency-blocked checkpoints below are historical and superseded.

New prediction/ml_development.py, scripts/train_nmcs_development.py and
 tests/test_ml_development.py implement strict cutoff loading, fixed raw schema,
train-only preprocessing, four bounded candidates, identical-cohort comparison,
paired tail/time uncertainty and local provenance. Detailed measured report:
NMCS_MODELING.md. No approved readiness, API, simulator, SQL, frontend, Render,
Phase 05A implementation, decision or dependency-pin changes.

The existing fictional dataset manifest ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b
and approved scientific versions were checked before fitting. Only timestamps/status
records through 2024-11-20 were admitted. No calibration/test status, prevalence or
performance was decoded. Prior baseline JSON is TRAIN-only and hash-verified;
only prior development_replay evidence was decoded, not full-world statistics.
Fresh training-cutoff reconstruction blocks future global-end label extension.

Pre-fit plan: training references every 14 days with one label-blind seeded offset
per available ten-day bin, all H=1..180 supported; 208800 examples / 7412 positives,
reference 2020-11-21..2023-11-18, final TRAIN outcome 2023-11-20. Development:
4320 identical examples/H, ten required/arbitrary H, 43200 rows; references
2023-11-21..2024-05-21, last outcome 2024-11-17. Correlated rows are not independent
failures. Raw missing inspection/phase fields dropped using TRAIN only; other
numeric TRAIN medians/missing indicators/scaling and TRAIN one-hot categories.

Four fixed candidates, seed 42017, one thread, no class reweighting/resampling:
L2 logistic C=.1/1, lbfgs tol1e-6 max1000; convergence 183/168 iterations, no warnings.
HistGradientBoosting log_loss, learning_rate .05, 150 iterations, 15 leaves/depth4
or 7/depth3, min_leaf200, L2=10, bins127, early_stopping=False. Fixed tree budgets
are not an optimality claim. All four produce valid predictions at every H=1..180
for current-NMCS and non-NMCS; no hidden future or tail-numeric features.

Actual macro Brier: recovery baseline .03042103, LR C=1 .03046244, LR C=.1
.03050050, HGB7 .03050349, HGB15 .03052928. LR C=1 is point-score best ML only,
not a champion: .1361% worse mean Brier and worse mean log loss (.138698 vs
.138467). Predeclared >=2% practical gain/reliability criteria fail. HGB15 H7
Brier .024700 vs recovery .025164, but paired interval includes zero. LR H180
Brier .035093 vs .035232, tiny gain; two time clusters cannot support a paired CI.
Retain persistence_recovery; NO ML CHAMPION. No automatic calibration progression
or promotion. Optional diagnostic calibration of frozen lr-c1 needs separate
chief-architect authorization. Calibration and locked test NOT RUN; Phase 05C NO-GO.

Actual commands from root (no publication):
- `.harness-test-tmp/phase05b-ml-env/Scripts/python.exe -B scripts/train_nmcs_development.py --experiment phase05b-ml-development-v2`: exit 0, 53.258 s feature preparation, 120.386 s total; four fixed configurations, no post-result tuning.
- `.harness-test-tmp/phase05b-ml-env/Scripts/python.exe -B -m unittest discover -s tests -p test_ml_development.py -v`: final 14/14 PASS, 4.068 s.
- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_nmcs.py -v`: 41/41 PASS, .777 s.
- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_readiness.py -v`: 28/28 PASS, 1.067 s.
- `powershell.exe -NoProfile -File scripts/verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable`: 229 run, 221 passed / eight new isolated-estimator-only skips, 0 failures/errors, 128.734 s. All eight execute in the isolated 14-test suite; old portable tests unchanged.
- `powershell.exe -NoProfile -File scripts/security_check.ps1`: exit 0, 87 tracked/index files, zero confirmed violations; ten existing benign leads retain documented dispositions.
- Explicit untracked source/test review using unchanged Inspect-Text: three new source/test files reviewed, zero extra leads.
- Git whitespace/protected-baseline checks: PASS; no frontend/build or unchanged harness failure-path suites rerun.

Artifacts in ignored .harness-test-tmp/phase05b-ml-development-v2: four own fitted
pipelines, pre-fit plan, development metrics/prediction CSV, frozen provisional
configuration and manifest. Model/evidence/source hashes verified without model
deserialization. Manifest SHA 689b0f5e8a5d5bc100f090bb5820125a83c0fdcda10d4b0ee4b8990ee368c938.
Runtime certificate a8595076b43fb3bacf32bf7301c0714820ff12764dfc48e871c2c70561520c43
is unchanged. One v1 attempt was stopped after feature preparation for a misplaced
pandas import; its plan/log/status remain. The import-only fix changed no candidates
or criteria; no v1 model results selected. Dataset never regenerated.

Existing ten benign security leads retain prior dispositions: SecretStr, runtime
settings and injected-secret bindings, loopback comparison, historical server-reuse
suffix match. Rules unchanged; scanning is not CVE certification. No actual
operational data or scientific claims from calibration/locked outcomes. Synthetic
associations and clipped-history/assignment limitations remain. Windows development
success is not Linux/offline-package/customer-release acceptance.


## Phase 05B dependency-independent preparation - 2026-11-24

PARTIAL / DEPENDENCY BLOCKED. Branch feature/05b-nmcs-modeling at required merged
PR #15 baseline cb12229071dcae580d636300b9119aaf4f5a1a48. Only preparation,
empirical baseline development and tests proceeded under the explicit fallback.
The existing CPython 3.13.7 .venv has NumPy 2.3.4/pandas 2.3.3; scikit-learn,
SciPy, joblib and threadpoolctl are absent, and no workspace modeling environment
or wheel bundle was found. No installs/upgrades/downloads or legacy model loading.
Logistic/boosted ML candidates, tuning, calibration and locked testing are NOT RUN.
Full Phase 05B scientific acceptance and Phase 05C are NO-GO until these gates
are completed. Only the dependency-independent preparation is eligible for a
clearly marked review PR after code/security gates; it is not ML completion.

New source: prediction/experiments.py (purged partitions, fixed raw feature schema,
three empirical probability baselines, metrics/cluster diagnostics and manifest
checks); scripts/prepare_nmcs_modeling.py (separate six-year preparation/replay,
verified data reuse); tests/test_experiments.py. Scientific contract/report and
actual artifact hashes: [NMCS_MODELING.md](NMCS_MODELING.md). Three governance
files updated. No Phase 05A, readiness, API, simulator, frontend, dependency,
SQL, deployment or other-worktree changes. Unrelated patches/launcher preserved.

Actual generation: one separate fictional 2020-11-21..2026-11-20 world, seed 42017,
160 tails/four commands/four platforms, 2,191 days/350,560 aircraft-days; 1,361 NMCS
runs, 12,950 NMCS days (3.694089%). Completed duration n=1,354, mean 9.5325 days;
seven right-censored runs. All 180 label counts measured; H=180 eligible 321600,
positive 11843. Inspection/phase are both missing in the event projection. Complete
30/90/180/365 windows: 345760/336160/321760/292320 reference-tail pairs.

Actual experiment commands (root, existing .venv):
- `.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py`: exit 0, 47.640 s.
- `.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py --reuse-dataset phase05b-six-year-42017-v1 --output-name phase05b-six-year-42017-v2`: exit 0, 22.601 s; numerical tie guard, no regeneration.
- `.venv/Scripts/python.exe -B scripts/prepare_nmcs_modeling.py --reuse-dataset phase05b-six-year-42017-v2 --output-name phase05b-six-year-42017-v3`: exit 0, 26.152 s; added feature-completeness counts, no regeneration.

All runs/evidence retained; dataset and empirical-parameter hashes are identical
across the three runs. Final ignored directory .harness-test-tmp/phase05b-six-year-
42017-v3 contains CSV, baseline JSON, development report and versioned manifest.
Manifest SHA-256 ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b;
source revision plus exact working-source hashes recorded, no false clean-code claim.
No trained ML artifact exists. Artifact integrity and source-hash checks PASS.

Development replay: train 2020-11-21..2023-11-20; validation 2023-11-21..2024-11-20;
calibration and locked test each reserve a following year and are not scored/fitted.
Common weekly cohort: 27 dates x 160 tails = 4320 examples per horizon/method,
purged at H=180. Checkpoints 7/30/60/90/120/150/180 plus 14/45/123. H=7 occupancy/
recovery Brier 0.028358/0.025164; H=180 0.035237/0.035232 (tiny difference).
Current-NMCS/recovered tails included; group/calibration/lift/fleet counts and
exploratory tail/time-cluster intervals are reported. Seven 28-day time clusters
are too few for strong long-horizon claims; no paired superiority/ML/calibration/
accuracy/customer-release acceptance is asserted.

Actual verification:
- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_experiments.py -v`: final 19/19 PASS, 0.263 s; deterministic empirical fitting, cutoff/schema/integrity/probability checks and numerical ranking guard.
- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_nmcs.py -v`: 41/41 PASS, 0.820 s.
- `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_readiness.py -v`: 28/28 PASS, 1.180 s.
- `powershell.exe -NoProfile -File scripts/verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable`: initial 214/214 PASS, 165.017 s; final 215/215 PASS, 160.352 s; zero failures/errors/skips.
- `powershell.exe -NoProfile -File scripts/security_check.ps1`: pre-stage exit 0; 83 tracked/index files, zero confirmed violations, ten existing benign leads; mandatory post-staging result in publication evidence.
- Explicit untracked source/report review with unchanged Inspect-Text rules: four new source/report files explicitly scanned, zero additional leads.
- `git diff --check` and protected-baseline comparison: PASS; only the reviewed seven preparation files may be staged.

The final portable run follows a new numerical-stability test/code correction.
Five external-reference cases remain excluded there; the separate 28-test baseline
includes original parity cases. No frontend/browser/build or unchanged harness
failure-path suites repeated. Raw logs .harness-test-tmp/phase05b-* stay ignored.

Existing ten benign security leads retain their dispositions below (SecretStr,
runtime settings/injected-secret bindings, loopback comparison and historical
server-reuse suffix match). No rules weakened. Heuristic scanning is not a CVE
attestation. The new fictional artifacts are not in the index or Docker context.
To continue: approve/provide a separately pinned scientific environment or audited
wheel bundle; then implement the actual candidate estimators, train-only transforms,
calibration and independent locked evaluation. No app/runtime dependency change is
authorized by this missing-dependency report. Full six-year warm-up cannot be
claimed for early references; dataset/history/assignment limitations remain explicit.


## PR #15 automated review corrections - 2026-11-24

Two confirmed defects corrected on feature/05a-nmcs-foundation from 9e20f88:
(1) target/coverage admitted sparse reference days that features rejected; all
three now share a cutoff-safe reference_at policy and immutable fleet observation-
date index; (2) rolling-window known starts discarded the preceding usable day.
Starts now use that context without adding it to window-day counts; ongoing NMCS
and unknown predecessors remain censored. No backend, simulator, formula,
frontend, dependency, training, model, SQL or deployment changes.

Six new regressions: pre-fix focused run 41 tests, 19 failing assertions, exit 1;
after correction 41/41 PASS, 1.122 s, exit 0. Same exact focused command:
`.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_nmcs.py -v`.
Protected command `.venv/Scripts/python.exe -B -m unittest discover -s tests -p
test_readiness.py -v`: 28/28 PASS, 1.220 s, exit 0.
Final `powershell.exe -NoProfile -File scripts/verify.ps1 -PythonExecutable
C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable`: 196/196 PASS, 146.161 s, exit 0; zero failures/errors/skips; five
external-reference tests excluded from this portable run.
Mandatory staged `powershell.exe -NoProfile -File scripts/security_check.ps1`:
final result is recorded in the PR review-correction publication evidence.
Existing ten benign scanner leads retain their dispositions below; no rule changes.
Staged whitespace, exact six-file correction scope and protected-baseline checks
are required before commit. No unrelated suites are repeated.

Reassessed with `.venv/Scripts/python.exe -B scripts/assess_nmcs.py`: exit 0,
15.621 s. Coverage unchanged: 160 tails, four commands, 1,461 days/233,760 tail-days,
10,273 sparse events, 872 NMCS runs, zero initially left-censored NMCS. At every
H=1..180, eligible count falls by 160 because one fleet observation-gap reference
cannot produce as-of features. Correct dataset-specific formula is 160*(1460-H).
H=1/7/30/90/180: eligible 233440/232480/228800/219200/204800; NMCS positives
8132/8103/7995/7602/7028. The original figures below are historical and superseded
for eligible/positive counts only. No simulator or target-date meaning changed.
Corrected contract: NMCS_FOUNDATION.md. Original logs preserved; new evidence uses
.harness-test-tmp/phase05a-review-*. Six-year/real-source/ML release gates stay open.
No merge, deployment, training or other-worktree changes are authorized.


## Phase 05A NMCS foundation - 2026-11-24

Branch feature/05a-nmcs-foundation; baseline origin/main
1565e7b82c09e9bd263f29e8c8ae292d1b5eeee6. Main advanced from expected d4d11b4
by README title only, inspected and reported before implementation. PR #14 is merged
in this baseline; older open-PR statements below are historical checkpoints.
No claim that Render was deployed or hosting acceptance completed.

Implemented pure exact-date NMCS occupancy labels (H=1..180), strict normalized
observation/daily reconstruction, explicit carry validation, null censored targets,
as-of-safe history features and aggregate fictional coverage assessment. Current
NMCS remains eligible; NMCM is never the positive target. Separate six-year requested
reference, missing-hours flags and gap/episode censoring are explicit. No readiness,
API, dashboard, simulator, SQL, legacy artifact or deployment implementation changes.
Contract, source assumptions and feasibility: [NMCS_FOUNDATION.md](NMCS_FOUNDATION.md).

Actual commands from repository root (existing .venv; no installs):

| Command | Actual result |
|---|---|
| `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_nmcs.py -v` | Final source: 35/35 PASS, 1.064 s; zero failures/errors/skips |
| `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_readiness.py -v` | 28/28 protected Phase 01 tests PASS, 1.381 s, including five original source-backed parity cases |
| `.venv/Scripts/python.exe -B scripts/assess_nmcs.py` | Exit 0, one generation/validation/assessment in 16.32 s; 160 tails/four commands; 1,461 days/233,760 tail-days; 872 separate NMCS runs; no initial left-censored NMCS; all 180 horizon counts reported |
| `powershell.exe -NoProfile -File scripts/verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable` | Initial source: 187/187 PASS, 170.714 s; final source: 190/190 PASS, 214.568 s; zero failures/errors/skips |
| `powershell.exe -NoProfile -File scripts/security_check.ps1` | Pre-stage exit 0, 78 index/working files, zero violations; final staged: mandatory staged result recorded in the PR publication evidence |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --cached --check` | PASS, exit 0; exact eight-file scope |
| Protected baseline comparison against 1565e7b | PASS: original APIs/providers/simulator/readiness/tests, FIS decisions, Windows/frontend/deployment dependencies and runtime files unchanged |

The final portable rerun is necessary because three focused tests and final cache-read
source changed after the first gate. Five external-reference tests are intentionally
excluded from that run; the separately required 28-test Phase 01 run includes
those original source-backed cases. No model/SQL access or operational records.
No unrelated frontend/browser/build suites
or engineering-harness failure-path tests rerun: their implementation is unchanged.
Raw aggregate evidence/logs stay ignored under .harness-test-tmp/phase05a-*.

Security dispositions: ten existing benign leads (five expressions in index and
working tree): config.py:30 SecretStr declaration; providers.py:86 runtime settings
binding; providers.py:89 injected-secret binding; dashboard.spec.ts:14 loopback
hostname comparison; historical PROJECT_STATE server-reuse suffix match. No live
credential/operational endpoint. Five new untracked source/test/contract files were
explicitly scanned with unchanged Inspect-Text rules: zero additional leads.
Scanner REVIEW REQUIRED is retained and dispositioned; not a CVE attestation.
Unrelated pre-existing patches/local launcher are not reviewed for publication and
remain excluded. All existing worktrees/evidence preserved.

CONDITIONAL GO for separately approved offline fictional Phase 05B model experiments
only. Six-year data generation, exact compatible ML dependencies, training-fold-only
preprocessing, purged temporal splits and independent per-horizon evaluation remain
future work. No accuracy, probability, rules, inference or customer-release claim.
Real-source calendar, duplicate ordering, active population, current-assignment
leakage, target-gap validation and hours mapping remain blockers for operational
integration. This NMCS-only instruction authorizes no NMCM prediction; prior
potential separate-NMCM release text is not the scope of Phase 05A. Fresh Linux
runtime/memory/cold-start/functional and Windows offline acceptance remain required
before any later customer ML release.


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


## Historical Docker/Render preflight evidence - 2026-11-23

Detached deployment worktree at merged main 8ad8f9173429672b04957d3ee381851422dc5eae;
remote main verified unchanged. Existing runtime/context files and running localhost
container preserved; no rebuild/install/source changes. Report:
[deploy/demo/PREFLIGHT_REPORT.md](../deploy/demo/PREFLIGHT_REPORT.md).

Prior build/native/pip-check and browser evidence recovered. Local normal readiness
33.43 s; constrained 0.5 CPU/512 MiB readiness 94.12 s, peak 276.64 MiB, warm 217.77
MiB; clean stop exit 0. Nine missing constrained browser checks pass in 24.5 s,
with old output preserved. Served assets and all application-source hashes match
the retained image. No SQL, models, operational data or secrets in reviewed app
artifact. HTTP source paths/default docs routes remain blocked.

Security exit 0: 71 tracked/index files, zero confirmed violations, 10 existing
benign leads dispositioned in the report; six untracked POC/report files explicitly
reviewed/scanned with zero additional leads. Git whitespace/protected-file checks
pass; five original POC file hashes preserved. No broad suites repeated.

**Superseded recommendation (retained as historical evidence):** The following
Starter/cost and test-portability requirements are no longer current. Render Free
and Git-backed Docker supersede the paid candidate; portable tests and PR
publication are complete. CVE, actual Render and Windows offline acceptance remain
open. Original measurements and security evidence above are unchanged.

Recommendation CONDITIONAL GO only: approve access protection and Starter-class
compute cost before hosting; no authentication claim. Current Render account/service
configuration has not been accessed. No registry push/public deployment. POC test
portability, CVE/supply-chain review, actual Render smoke tests and Windows offline
acceptance remain open. No formula, React, simulator, provider, ML or canonical
Windows dependency changes. No staging, commits, branch changes or publication.

## P0 command-filter correction and acceptance audit - 2026-11-23

Starting branch `main`, HEAD `79c3360ae8ea4e170fa1452dbc54383de02304aa`.
This customer instruction supersedes the previous task's fleet-always presentation
and test oracles. The earlier entry remains historical evidence, not current
reporting behavior. Pre-existing untracked review patch and local launcher remain
excluded and untouched. No staging, publication, dependencies or backend changes.

### Root cause and correction

The prior implementation incorrectly interpreted retaining the overall fleet
summary as keeping it authoritative after command selection. App constructed an
overall snapshot for history and ReadinessPanels used `data.overall ?? data` for
KPIs, counts and status distribution. The API had already returned the correct
selected-command snapshot; React chose the wrong object. Static FLEET labels and
Fleet overview heading compounded the misleading scope. These related presentation
defects are now corrected; no backend calculation defect was found.

App now passes `view.data` directly to both panels and HistoricalTrends. Panels
use the selected fleet/report object and distribution directly. KPI labels and
heading identify the selected command, and the scope indicator remains truthful
on loading/error states. All Commands selects the consolidated fleet snapshot.
The internal Dashboard type no longer exposes an overall property, preventing
that display escape path. The loader retains private unfiltered responses only
for fleet-to-command count validation, not as UI fallback or percentage oracles.

Nested command/platform details, six-status partitions, NMC count, date/windows,
request cancellation and stale/source guards remain unchanged. Serviceability and
availability are API-owned values, neither computed nor averaged in React.
FIS-001/FIS-002/FIS-003, readiness/history engine, simulator and backend contracts
are unchanged. No Python/backend/portable/harness suites were repeated for this
frontend-only correction.

### Why the previous tests accepted the defect

- App.test command-filter assertion was explicitly changed to expect fleet 83.3%
  after selecting B instead of B's 66.7%. It asserted incorrect product behavior.
- history.test expected an unfiltered history URL after command selection.
- platform component/browser cases expected 160 tails and compared the main cards
  with an unfiltered fleet response after selecting a command. These were wrong
  acceptance oracles even where they used real HTTP responses.
- Shared history fixtures assigned identical 82.75/71.25 percentages to fleet and
  every command, and equal command populations, masking wrong-scope consumption.
- API unit tests proved correct request parameters but did not prove that React
  consumed the selected response. Counts of passing tests did not establish parity.

All incorrect assertions identified above are replaced with selected-command
expectations. Dedicated acceptance fixtures deliberately separate fleet, A and B
percentages and all six status populations. Those values are explicit API-shaped
test values, not a second readiness calculator. Existing equal-value fixtures are
retained for narrow mechanics tests; they are no longer the scope acceptance oracle.
No unrelated reporting defect was confirmed by this audit. It does not claim an
exhaustive proof of all possible reporting combinations.

### Requirement-to-test matrix

| Requirement | Specific evidence | Mechanism and limit |
|---|---|---|
| Fleet reporting | scope.test: selected A, selected B and All Commands; history.spec: acceptance demonstration | Component fetch mock plus actual synthetic HTTP/browser; verifies fleet KPIs/counts/statuses/history before and after filters |
| Command reporting | scope.test: selected A/B; App.test: applies a command filter; history.spec: acceptance demonstration | Distinct fictional API mock plus real HTTP responses/UI; positive and negative KPI/population/scope assertions; other command absent |
| Nested platform reporting | command.test: renders each command once; platform.spec: each command appears once and independently owns reconciled platform counts and trends; scope.test: selected A/B | Component mock and real HTTP/browser; owning-command platform requests, independent selections, unique IDs and all partition sums |
| Reporting date | scope.test: date and all windows retain command B; history.spec: all windows and command/date filters stay aligned | Mock request parameters plus browser/actual selected-command backend response; dates pinned to API snapshot |
| History/windows | scope.test: date/all windows; switching A to B; unavailable command B history; history.spec: actual HTTP scope demonstration | Component mock with delayed/rejected responses plus actual browser series/point geometry; selected command on every 30/90/180/365 request, no stale/fleet chart |
| Reset/navigation | scope.test: date/all windows/reset; App.test: date selection/reset; dashboard.spec: live filter reset and keyboard navigation | Mock and real HTTP/browser; All Commands preserves selected date; Latest snapshot resets date and command. Browser Back/URL routing is not implemented or claimed |
| Reconciliation/source isolation | command.test: inconsistent populations and collapsed late SQL; platform.test contract/source/cancellation cases; api.test SQL health; browser history/platform error/source cases | Mock fetch and browser HTTP fault injection, plus real synthetic partition reconciliation; actual SQL and authentication remain untested |

### Execution evidence

All npm commands run from `frontend/` with installed dependencies only and prefix:
`npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache`.

| Suffix | Actual result |
|---|---|
| `test -- src/scope.test.tsx` before runtime correction | Exit 1: three failed/four passed. Expected A 78.1%, received fleet 83.1%; command A history request absent. Proves the new tests detect old behavior |
| `run check` | Initial new-test option typing error corrected; subsequent PASS, exit 0 |
| `test -- src/scope.test.tsx src/App.test.tsx src/history.test.tsx src/platform.test.tsx` | PASS, exit 0; 110/110, four files, 36.50 seconds |
| `test` | Intermediate PASS, 135/135; final strengthened regression: PASS, exit 0; 136/136 in six files, 48.57 seconds |
| `run build` | PASS, exit 0; tsc --noEmit, Vite 8.3.8, 20 modules, 286 ms |
| `run test:e2e -- --config=../.harness-test-tmp/command-centric/playwright-isolated.config.mts` | PASS, exit 0; 47 passed/four intentional skips, 51 total, zero retries, 2.2 minutes |

The final screenshot review additionally found the availability description still
saying total fleet for a selected command. That scope-label defect is corrected
and explicitly asserted. After this text-only source change, eight/eight acceptance
tests passed (exit 0, 13.71 seconds), production TypeScript/build passed (exit 0,
20 modules, 308 ms), and the affected three browser demos passed (exit 0, three/three, no retries/skips,
1.2 minutes). Exact additional suffixes: `test -- src/scope.test.tsx` and
`run test:e2e -- --config=../.harness-test-tmp/command-centric/playwright-isolated.config.mts --project=history-desktop --project=history-tablet --project=history-mobile --grep "acceptance demonstration"`.
Final screenshots were regenerated; the final desktop B image was visually inspected.
The complete 136/47 results above precede only this descriptor change. The four
browser skips are the original/platform touch cases on non-mobile projects; both
actual mobile touch cases passed. Both themes/keyboard and nested-platform cases
remain in the full browser suite.

The established ignored wrapper owns CSV API/Vite 18000/15173 and history API/Vite
8001/5174, all loopback with server reuse disabled. It does not stop or reuse the
user's local launcher. No external services or downloads. Logs are under ignored
`.harness-test-tmp/command-scope/`. Build: HTML 0.62 kB, CSS 16.72 kB (gzip 4.48 kB),
Final JS 255.25 kB (gzip 77.95 kB). No runtime source changed after the final build.

### Actual browser before/after scope demonstration

On 2026-11-20 fictional synthetic history, the actual UI network fleet/distribution/
history responses were inspected for All -> A -> B -> All. UI values, every count
card, all six status rows and every plotted serviceability point match responses.
API serviceability/availability values were compared directly, never recalculated.

| Transition | Displayed serviceability | Displayed availability | Tails | FMC/PMCM/PMCS/NMCS/NMCM/DEPOT |
|---|---|---|---|---|
| Initial All | 94.6% | 88.1% | 160 | 135 / 2 / 4 / 7 / 8 / 4 |
| Select A | 92.3% | 90.0% | 40 | 35 / 0 / 1 / 1 / 3 / 0 |
| Select B | 94.4% | 85.0% | 40 | 34 / 0 / 0 / 4 / 2 / 0 |
| Restore All | 94.6% | 88.1% | 160 | 135 / 2 / 4 / 7 / 8 / 4 |

Recorded history requests use end_date=2026-11-20 and days=30, with command absent
for All and respectively command=FICTIONAL_A / command=FICTIONAL_B. Each returned
30 points for its scope. This is an observed fixed-browser sequence, not a claim
that a pre-fix browser demo was run; the pre-fix failure evidence is the unit run.
Raw responses/request URLs and screenshots remain local ignored evidence:
`frontend/test-results/history-acceptance-demonst-418f0-k-follows-actual-HTTP-scope-history-{desktop,tablet,mobile}/scope-evidence.json`
and `scope-{0-ALL,1-FICTIONAL_A,2-FICTIONAL_B,3-ALL}.png` in those same folders.

### Final file inventory and security review

Fourteen task files, all unstaged:

- docs/PROJECT_STATE.md, docs/TASKS.md, docs/RELEASE_GATES.md
- frontend/src/App.tsx, frontend/src/ReadinessPanels.tsx, frontend/src/api.ts
- frontend/src/App.test.tsx, frontend/src/history.test.tsx, frontend/src/platform.test.tsx
- frontend/src/scope.test.tsx (new), frontend/src/test/scopeFixtures.ts (new)
- frontend/e2e/dashboard.spec.ts, frontend/e2e/history.spec.ts, frontend/e2e/platform.spec.ts

`git diff --check` and protected-path comparisons pass (exit 0); index empty.
`& .\scripts\security_check.ps1`: exit 0; 69 tracked/index files, zero confirmed
violations, 10 existing manual leads (five expressions in index and working tree).
Dispositions: api/config.py:30 is a SecretStr declaration; api/providers.py:86 is
runtime settings binding; api/providers.py:89 is injected secret binding;
frontend/e2e/dashboard.spec.ts:14 is loopback hostname comparison; historical
PROJECT_STATE server-reuse text matches a scanner suffix. No embedded credential
or operational endpoint; all leads are benign and dispositioned. REVIEW REQUIRED
is the scanner's unchanged label, not an unresolved security violation.
The two new acceptance files were explicitly reviewed as regular text and scanned
with the scanner's Inspect-Text function extracted through PowerShell AST: zero
additional leads. Existing unrelated patch/launcher are excluded, untouched and
not proposed for publication. Staged security checks are deferred because staging
is prohibited. No security rules were modified.

### Review boundaries

Task changes are limited to frontend source/tests and these project records.
HistoricalTrends was inspected and retained unchanged; passing the selected snapshot
restores its existing command-aware request/validation path. No client formula,
SQL/provider, simulator, prediction, dependency or security-policy changes.
Physical devices/iOS/WebKit, full accessibility audit, browser Back/URL state,
actual SQL, operational cross-request consistency, authentication and offline
release acceptance remain unverified/deferred. Only fictional data were used.
No stage, commit, push, PR, merge or deployment. Stop for chief-architect review.

## Command-centric readiness implementation - 2026-11-23

Customer-authorized frontend implementation in the existing `main` working tree;
starting HEAD `fd6ca4d05736aa2bfb73daab7b40fc02eb5b9232`. No staging/publication.
The pre-existing untracked `run_fis4_local.py` is excluded from this task and untouched.

### Implemented behavior and existing API reuse

Overall fleet KPI/count/distribution and history remain fleet-wide for the selected
date, including when a command filter narrows the command list. Each command has
one primary summary showing API-owned Serviceability/Availability, NMCS, NMCM,
NMC Total (the count NMCS + NMCM), DEPOT and retained FMC/PMC/tail counts. No
readiness percentage is calculated or averaged in React.

The standalone fleet-wide platform interface is removed. Each command owns native
keyboard-operable details/summary. Expansion loads its six-status distribution,
platform list and comparison for that command/date only; selected platform history
always includes the owning command, end date and shared 30/90/180/365-day window.
Several commands can be expanded independently. Unique React IDs prevent control
label collisions; the shared chart/touch behavior is reused unchanged. Collapsing
unmounts details and aborts requests. Reopening refetches rather than retaining
unbounded per-command caches. All names/associations remain fictional; battalion
and internal hierarchy fields are absent from normal presentation.

Existing endpoints only, with no backend/query/response contract changes:

- `/api/v1/readiness/commands`, `/api/v1/readiness/fleet`, `/api/v1/status-distribution`
- `/api/v1/platforms?command=...`
- `/api/v1/readiness/history/platforms?date=...&command=...`
- `/api/v1/readiness/history/platforms/series?end_date=...&days=...&platform=...&command=...`
- Existing fleet history-series route remains fleet-scoped in the top overview.

The typed loader retains selected-command data and adds an internal overall
snapshot from existing unfiltered endpoints, pinned to the same API-resolved date.
It rejects fleet/command count mismatches, inconsistent selected command metrics
and six-status population inconsistencies. Expansion reuses API command metrics
and obtains PMCM/PMCS separately from its distribution before validating platform
partitions. No percentage reconstruction or new tail/population constants added.
Existing bounded platform responses, SQL blocking, safe errors and request identity/
abort guards remain. Default operational rendering never requests cross-command
platform aggregation. The existing backend still performs distinct-tail counting
and FIS-001 calculations with unchanged historical reconstruction.

### Executed verification

From `frontend/`, exact npm prefix:
`npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache`.

| Suffix | Actual result |
|---|---|
| `run check` | PASS, exit 0 |
| `test -- --run src/api.test.ts src/platform.test.tsx src/App.test.tsx src/history.test.tsx` | Initial 120 passed/two failed (lazy-mount test waits); assertions corrected |
| `test` | PASS, exit 0; 128/128 across five files, 36.99 seconds |
| `test -- src/command.test.tsx` | Strengthened final command tests: six/six PASS, exit 0, 6.65 seconds |
| `run build` | Final PASS, exit 0; includes TypeScript, Vite 8.3.8, 20 modules, 488 ms |

Build outputs: HTML 0.62 kB, CSS 16.72 kB (gzip 4.48 kB), JS 255.16 kB
(gzip 77.97 kB). Outputs/logs/cache/browser artifacts stay ignored. Six new tests
cover unique/lazy command rows, NMC counts, independent platform values and trends,
control IDs, fleet/command/status reconciliation failures and collapse cancellation.
All original 122 cases remain with expectations adapted to nested presentation and
permanent fleet overview. Fictional CSV fixtures now reconcile across dates and
command distributions; readiness percentages remain explicit fixture values.

Browser verification: PASS, exit 0; 44 passed/four intentional skips, 48 total,
2.4 minutes, zero retries. The original 45 cases remain and the new command-owned
reconciliation case runs across history desktop/tablet/mobile. Skips are only the
original and platform mobile-touch cases on desktop/tablet. Both mobile touch cases
pass in light/dark themes, requiring real CDP swipe scroll movement. Tests verify
every command appears once, same-platform independent rows/trends, fleet-to-command
six-status sums, every window, keyboard expansion/inspection, no duplicate IDs,
stale/SQL safety and no page overflow. Desktop-light and mobile-dark platform
screenshots were visually reviewed. Nine platform/nested-command screenshots remain
local ignored evidence in `frontend/test-results/` (six theme images and three
all-command images).
The initial normal command `run test:e2e` stopped before tests because the user's
local launcher owns 8000/5173. Those processes were not stopped or reused. An ignored
local wrapper config moves owned CSV API/Vite to 18000/15173, keeps history API/Vite
on 8001/5174, all on 127.0.0.1, with server reuse disabled. The first wrapper startup
failed because its history Vite command inherited the config-folder cwd; the ignored
wrapper now explicitly supplies frontend cwd. No tests ran in either startup failure.
Exact browser suffix: `run test:e2e -- --config=../.harness-test-tmp/command-centric/playwright-isolated.config.mts`.
Logs/configs: `.harness-test-tmp/command-centric/` (local ignored evidence).

### Git and security verification

`git diff --check` passes (exit 0). Protected-path comparison to HEAD passes;
the Git index remains empty. Existing history bytes in governance documents are
preserved; an intermediate Windows text-encoding issue in the new documentation
write was corrected before final checks. No existing historical evidence changed.
The React review checklist was applied to effect cleanup, derived view identity,
per-instance IDs, lazy mounting and reused accessible chart controls.

`& .\scripts\security_check.ps1`: exit 0, 68 tracked/index files, zero confirmed
violations and 10 existing manual leads (five expressions, each in index and working
tree). Dispositions: api/config.py:30 is a SecretStr field declaration;
api/providers.py:86 binds runtime connection settings; api/providers.py:89 binds an
injected secret; frontend/e2e/dashboard.spec.ts:14 is a loopback hostname equality;
the historical PROJECT_STATE server-reuse setting matches a scanner suffix. None
contains an embedded credential, real database address or operational record. All
five causes are benign, all ten leads dispositioned; the scanner reports REVIEW
REQUIRED by design. Its rules are unchanged. The new command test is explicitly
reviewed/scanned with the same Inspect-Text rules because it is untracked; zero
additional leads. The user's unrelated untracked launcher is excluded, not proposed
for publication and not modified. Future publication still requires staged checks.

### Scope and acceptance limits

Task inventory (16 files):

- frontend/src/App.tsx, frontend/src/ReadinessPanels.tsx,
  frontend/src/PlatformIntelligence.tsx, frontend/src/api.ts, frontend/src/styles.css
- frontend/src/App.test.tsx, frontend/src/history.test.tsx,
  frontend/src/platform.test.tsx, frontend/src/command.test.tsx (new),
  frontend/src/test/fixtures.ts
- frontend/e2e/dashboard.spec.ts, frontend/e2e/history.spec.ts,
  frontend/e2e/platform.spec.ts
- docs/PROJECT_STATE.md, docs/TASKS.md, docs/RELEASE_GATES.md

Backend/provider/SQL views/simulator/readiness engine/protected tests, dependencies,
FIS-001/FIS-002/FIS-003 and approved architecture contracts remain unchanged.
No backend/portable/harness suites repeated: this task changes frontend only.
Physical devices/iOS/WebKit, full accessibility audit, real SQL, authentication,
prediction compatibility and offline release acceptance remain unverified. Refresh
and atomicity across separate live-production requests remain deferred backend
integration concerns; current immutable synthetic snapshots reconcile explicitly.
No API deficiency blocks this UI. No real data, database/model access, dependencies,
external services, staging, commits or deployment. Await chief-architect source review.

## Phase 03C-1B.2 frontend verification - 2026-11-22

Branch `feature/phase03c1b-react-platform`, unchanged HEAD
`693c7b56aa894de98ebd6730e811864d5f45edca`. All changes remain unstaged.
The nine implementation files are preserved. This step changes tests/fixtures,
browser discovery and three project records. No runtime correction was necessary.

All npm commands below ran from `frontend/`, using installed dependencies only.
Exact prefix: `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache`.

| Suffix after prefix | Actual final result |
|---|---|
| `run check` | PASS, exit 0; tsc --noEmit |
| `test` | PASS, exit 0; 122/122 tests in four files, 29.03 seconds |
| `run build` | PASS, exit 0; Vite 8.3.8, 20 modules, 447 ms |
| `run test:e2e` | PASS, exit 0; 41 passed/four skipped, 45 total, 2.1 minutes, retries 0 |
| `run test:e2e -- --project=history-desktop --project=history-tablet --project=history-mobile --grep 'actual platform comparisons\|command/date/platform'` (the shell argument uses a plain pipe, without the Markdown escape) | PASS, exit 0; strengthened follow-up six/six, 1.2 minutes, zero skips/retries |

The original 61 unit tests remain; 61 platform cases were added. Coverage includes
all three platform APIs; fleet/command populations; six statuses and PMC/count
reconciliation; all windows/clipping; date/command/platform alignment; malformed,
incomplete, internal-field and oversized responses; 404/422/503/network errors;
source/header disagreement, unsupported CSV endpoints, SQL blocking, cancellation
and stale completion. Deliberately distinct API percentage fixtures prove returned
values are displayed rather than recalculated. Selection preserves both overview
percentages and command-card content. Count validation and chart geometry are not
client-side readiness formulas. No fallback synthetic observations were added.

Browser tests use installed Edge and Playwright-owned loopback CSV/history API and
Vite servers. New cases check actual synthetic API contracts, all four windows,
combined selections, delayed/cancelled responses, retry/source blocking, keyboard
inspection and both-theme contrast (at least 4.5 for checked platform controls/text).
Viewports: 1440x1000 desktop, 768x1024 tablet, 390x844 mobile. Four intentional skips:
the original and new mobile-only touch cases each skip desktop and tablet. Both
mobile touch tests pass. The new case sends CDP touch start/move/end gestures to
the platform plot and comparison table in both themes, requiring horizontal motion
over 60 pixels without assigning scroll offsets. No page-wide overflow was observed.

Six final platform screenshots were regenerated and visually inspected:
`frontend/test-results/platform-actual-platform-c-14fb5-themes-keyboard-stay-usable-history-{desktop,tablet,mobile}/platform-{light,dark}.png`.
These reflect final runtime source and remain local ignored evidence. Build outputs
are also ignored: HTML 0.62 kB, CSS 16.41 kB (gzip 4.42 kB), JS 252.65 kB (gzip
77.31 kB). No runtime source changed after the passing build.
Local logs: `.harness-test-tmp/phase03c1b2/` (ignored).

### Failure history and targeted corrections

- Initial unit suite: 57 pass/four fail. Old fixtures lacked platform endpoint
  handling and old heading/alert assumptions needed the new identity/section.
  Explicit unsupported fixtures and scoped assertions preserve original coverage.
- New test compilation found unused import/unsupported query options and incorrect
  nested HTMLElement queries; corrected tests only. One check from repository root
  failed with missing package.json; corrected working directory immediately.
- Expanded unit suite: 117 pass/five fail (ready waits/ambiguous caption), then
  120 pass/two fail (ambiguous headers/new heavy four-window test timeout). Scoped
  selectors and async waits fix these; only the new four-window test has a 15-second
  timeout, with all assertions retained. Final complete run: 122 pass.
- First full browser run: 29 pass/12 fail/four skip. Old global table/window
  selectors became ambiguous with the new section. Exact/scoped selectors fix
  those tests without removing assertions. Full rerun: 41 pass/four skip.
- Stronger availability/command-card preservation assertions were then added.
  First six-case follow-up: three pass/three fail, caused by comparing innerText
  with DOM text. The assertion now compares textContent consistently; corrected
  follow-up six/six pass. No application defect was demonstrated by these failures.
- Final Git whitespace review identified a mixed-ending new TASKS row; corrected
  documentation line endings before the final check.

### Final scope and security review

17 pending files (four new), all unstaged:
docs/PROJECT_STATE.md, docs/RELEASE_GATES.md, docs/TASKS.md;
frontend/index.html, frontend/playwright.config.ts, frontend/e2e/history.spec.ts,
frontend/e2e/platform.spec.ts (new), frontend/src/App.tsx,
frontend/src/HistoricalTrends.tsx, frontend/src/PlatformIntelligence.tsx (new),
frontend/src/api.ts, frontend/src/styles.css, frontend/src/history.test.tsx,
frontend/src/platform.test.tsx (new), frontend/src/test/fixtures.ts,
frontend/src/test/historyFixtures.ts, frontend/src/test/platformFixtures.ts (new).

Security command: `& .\scripts\security_check.ps1`; exit 0, 64 tracked/index files,
zero confirmed violations, 10 existing manual leads (five expressions in index
and working tree). All dispositioned after source review:

- api/config.py line 30: SecretStr password field declaration, no embedded value.
- api/providers.py line 86: runtime server binding, no embedded database endpoint.
- api/providers.py line 89: injected secret binding, no embedded value or logging.
- frontend/e2e/dashboard.spec.ts line 14: loopback hostname equality, benign scanner
  expression match, not an operational endpoint.
- docs/PROJECT_STATE.md historical server-reuse setting: scanner matches the suffix
  of a local test setting; no database endpoint or secret. Historical evidence is
  retained unchanged. Each expression generates two leads; none is unresolved.

Four untracked TS/TSX files were explicitly reviewed as ordinary text (no links,
NUL or oversized files) and scanned using the unchanged scanner's Inspect-Text
function extracted through PowerShell AST: zero additional manual leads. Scanner
rules were not edited. The scanner still reports REVIEW REQUIRED; the documented
human dispositions above resolve these leads, not a change to scanner behavior.
Final `git diff --check` and protected-file comparison to HEAD passed (exit 0).
The index is empty; generated build/browser/log/cache outputs are confirmed ignored.

Backend, simulator, readiness engine, protected tests, FIS-001/FIS-002/FIS-003,
contracts and dependency manifests/lockfile remain unchanged. Runtime clients use
fixed same-origin paths; browser requests are constrained to loopback; no runtime
CDN or external service is introduced. No internal hierarchy fields are displayed.
Backend/portable/engineering-harness suites are deliberately NOT RUN under this
frontend-only task. Earlier 160/155/12 results remain historical, not new evidence.
Physical devices/iOS/WebKit, comprehensive accessibility audit, actual SQL,
prediction compatibility, authentication and FIS-002 offline acceptance remain
unverified/deferred. No installation, staging, commit, push or deployment occurred.
Stop at chief-architect review.

## Phase 03C-1B.1 React Platform Intelligence implementation - 2026-11-22

Branch feature/phase03c1b-react-platform, unchanged starting HEAD
693c7b56aa894de98ebd6730e811864d5f45edca (merged Phase 03C-1A backend).
The previous interrupted write was never executed; this step writes the assessed
frontend implementation directly in the existing working tree. It does not repeat
previous discovery or Python/backend/portable/engineering-harness verification.

### Implemented source behavior (runtime verification pending)

api.ts adds typed platform comparison/history clients for the three approved fixed
same-origin endpoints. Options/comparisons load in parallel using the effective
snapshot date and command. Responses require synthetic source/header consistency,
exact expected fields, allowlisted label syntax, finite percentages, safe integer
counts, all six statuses, PMC count consistency and current population reconciliation
against the actual snapshot. No new fixed 160/40 population assumptions are used
by platform validation. A streamed 262,144-byte limit bounds JSON before parsing;
comparison/list lengths cap at 32, daily series at 365. Dates/windows/order and
final-series-point equality to the selected comparison row are validated.
No readiness formula or averaging of percentages is implemented in React.

PlatformIntelligence.tsx adds a separate comparison table, platform selector and
platform history with shared 30/90/180/365-day window state. Selections affect only
this section, not existing fleet/command metrics or filters. Snapshot changes
cancel old platform requests; platform/window changes cancel old series requests.
Identity/key guards prevent stale rows or charts appearing under new selections,
even if transport completes late. Errors/retries are contained in this section;
SQL detection still invokes the existing whole-demo source block. Raw API details
and unexpected/internal fields are not displayed; no fallback observations exist.

HistoricalTrends exports its existing chart for reuse with optional platform
context, distinct labels/test IDs and a memoized daily table. Original Home/End/
arrow inspection, native slider, pointer behavior and touch-action auto remain.
CSS reuses existing light/dark tokens and locally scrollable tables/plots; mobile
controls stack. Product branding, page heading, footer, browser title and metadata
now identify Fleet Intelligence Suite / Fleet Intelligence Dashboard. The existing
fictional-data and unauthenticated-local-use notice is unchanged.

The React review checklist was applied by source inspection: effect cleanup and
stable source callbacks, derived selection state, no inline component definitions,
parallel independent fetches, memoized chart/table work, labelled controls and
focusable scroll regions. This is not executed accessibility/browser evidence.

### Checks and deferred verification

`npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run check`
from frontend passed (TypeScript tsc --noEmit, exit 0). The first check found two
assertion-narrowing errors in new validators; both were corrected. Final source
passed the focused check. No packages were installed.

By the user's explicit Phase 03C-1B.1 instruction, no Vitest, Playwright, production
build, backend, portable or engineering-harness suites were run. Prior backend
160/160, portable 155/155 and harness 12/12 are retained baseline evidence only,
not verification of this frontend. Tests/fixtures have not been modified in this
implementation step. Static Git/security review results are in the task response.

Phase 03C-1B.2 must add focused platform API/component tests and adapt existing
fixtures to the new requests and product identity. Browser assertions that use
global row/chart selectors must distinguish overall history from platform tables.
Verify count/status reconciliation, endpoint/source/header/payload bounds, all
windows, independent/combined selections, stale completion and abort behavior,
CSV/unsupported states, SQL blocking and raw-detail/hierarchy rejection. Run the
frontend typecheck/unit/build/relevant Playwright gates, both-theme desktop/tablet/
mobile and actual touch-scroll checks; capture new screenshots and security
findings. No runtime integration, responsiveness, accessibility, security acceptance
or frontend regression pass is claimed by this implementation-only step.

Files: frontend/src/api.ts, frontend/src/App.tsx,
frontend/src/HistoricalTrends.tsx, frontend/src/PlatformIntelligence.tsx,
frontend/src/styles.css, frontend/index.html; docs/PROJECT_STATE.md,
docs/TASKS.md and docs/RELEASE_GATES.md. Backend/simulator/readiness, dependencies,
FIS-001/FIS-002/FIS-003 and permanent architecture contracts remain unchanged.
All changes remain unstaged and uncommitted for chief-architect source review.

## Phase 03C-1A platform-aware historical backend - 2026-11-22

Branch feature/phase03c1-platform-intelligence, clean base
eda1baf20325675cab330b83e42145b2df1c6ac7. FIS-001/FIS-002/FIS-003, readiness.py,
original Python regressions, provider configuration/SQL implementation, all frontend
files and dependency pins remain unchanged. No network, SQL or model access.

Simulator schema 2 appends stable fictional platform metadata to aircraft/events;
no random draws or operational algorithms change. Default population remains 160,
four commands of 40, with four realistic platform labels spanning every command.
No battalion fields are needed or serialized. All original columns across all six
tables matched a Git-baseline 16-tail/365-day/seed-42017 run. The simulator's sparse
status-change/boundary reports remain distinct from working-day Production Control
observations; fictional parity fixtures test approved Streamlit reconstruction.

Three additive history-mode routes: /api/v1/platforms,
/api/v1/readiness/history/platforms and /api/v1/readiness/history/platforms/series.
List/comparison rows capped at 32; series at 365 points; all bodies at 256 KiB.
Strict allowlisted filters and generic errors; no internal hierarchy in responses.
Existing API models/routes and default CSV/SQL behavior remain unchanged.

One lifecycle cache adds immutable platform/command-platform records computed by
the approved readiness engine. Warm requests do bounded lookups only. Original
cache has 7,305 records; platform map adds 29,220 for this cutoff. No runtime or
production provider contract is constrained to that fictional distribution.

Focused command `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_platforms.py -v`
passed 21/21 in 46.542 s (exit 0). All 12 harness scenarios are retained; exact
counts now expect original 139 plus 21 = 160 full and 155 portable (five legacy
exclusions). Actual executed checks from the repository root:

| Command / check | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_platforms.py -v` | 21/21 passed, 46.542 s, exit 0 |
| `& .\scripts\verify.ps1 -PythonExecutable .\.venv\Scripts\python.exe` | 160/160 passed, 152.093 s, exit 0 |
| Same command with `-TestMode Portable` | 155/155 passed, 151.675 s, exit 0; five legacy-reference tests explicitly excluded |
| In-memory original-column comparison against Git HEAD simulator/contracts and generator | Six tables match for 16 tails/365 days/seed 42017, exit 0 |
| Exact protected-file comparison and `git diff --check` | Passed, exit 0 |
| Explicit new-file plaintext/link/size and existing Inspect-Text scan | tests/test_platforms.py reviewed; zero additional leads, exit 0 |
| `& .\scripts\security_check.ps1` | 63 tracked/index files, zero confirmed violations; 10 reviewed manual leads, exit 0 / REVIEW REQUIRED |

All test runs have zero failures/errors/skips. Full/portable runs above were
concurrent; their durations are suite execution measurements, not production or
cold-start benchmarks. Existing pandas/Starlette advisories remain unsuppressed.
No frontend/browser tests were run because React and frontend contracts are unchanged.

Every security lead is an existing expression seen in both index and working tree:

| Location (two leads each) | Disposition |
|---|---|
| api/config.py SecretStr declaration | No embedded credential |
| api/providers.py runtime server binding | Configured argument; no embedded endpoint |
| api/providers.py runtime credential binding | Injected secret; no embedded value or logging |
| frontend/e2e/dashboard.spec.ts hostname comparison | Loopback assertion; benign heuristic match |
| PROJECT_STATE.md historical Playwright-option text | Test-server setting; benign heuristic suffix match |

Scanner rules are unchanged. Untracked files are outside the standard scan, so the
new test was separately reviewed. No secrets, restricted SQL, operational records,
internal unit assignments or artifacts were introduced.

`& .\tests\test_engineering_harness.ps1 -PythonExecutable .\.venv\Scripts\python.exe`
completed with exit 0 and `HARNESS RESULT: PASS; Checks: 12`. Explicit and automatic
selection run all 160 tests; the final portable check passes 155 with five external
references excluded. Invalid-interpreter, failing/zero-test, security redaction,
prohibited-path/model and incomplete-inspection checks are preserved. No scanner
or protected regression expectations were weakened. Final documentation/Python
syntax, relative-link, whitespace and exact 13-file-scope checks pass; the index
remains empty. Final security reruns inspect the completed working tree; the new
untracked test is explicitly reviewed separately. No publication or staging occurs.

Changed inventory: api/history.py, api/main.py; simulator/contracts.py,
simulator/generator.py, simulator/__main__.py; tests/test_platforms.py,
tests/test_engineering_harness.ps1; README.md, docs/HISTORY_API.md,
docs/SIMULATOR.md, docs/PROJECT_STATE.md, docs/TASKS.md, docs/RELEASE_GATES.md.
Ready for chief-architect review of this local synthetic backend implementation;
no real integration or deployment acceptance is implied.

Unverified: physical SQL mapping/COALESCE/TLS/permissions, actual current hierarchy,
model/inference compatibility, production cold-start/load/multi-worker behavior,
authentication/access controls and FIS-002 offline deployment. The simulator does
not represent real platform-specific reliability or historical transfers/retirements.
No staging, commit, push, PR, merge or deployment is authorized by this task.

## Phase 03C-0 permanent Streamlit contract - 2026-11-22

Chief-architect documentation approval confirmed on 2026-11-22, including explicit
preservation of the view's inspection/phase-hours COALESCE behavior and separate
Streamlit readiness versus Enhanced1 prediction reconstruction requirements.
Prediction compatibility, physical SQL verification and deployment acceptance
remain unverified. Commit/push/PR publication is explicitly authorized by the user;
no merge or deployment is authorized. Prior local verification evidence below is
retained; no successful regression suites are repeated for publication.

Branch feature/phase03c0-streamlit-contract; clean starting commit
332c1db0f43b167693bc059d1e3897b01d1a27f4. Documentation only: two sanitized
contracts plus AGENTS.md, DECISIONS.md and this file. FIS-001/FIS-002, backend,
frontend, simulator, dependencies and regression expectations remain unchanged.

STREAMLIT_PARITY.md records customer-established view/organization requirements,
verified local source semantics and unresolved Enhanced1 inference compatibility.
INTRANET_INTEGRATION_CONTRACT.md records logical fields, provider safety and
exposure boundaries, future acceptance sequence and unchanged FIS-002 requirements.
FIS-003 records the baseline; AGENTS requires reading both contracts before relevant
code changes. No credentials, internal mappings, restricted DDL or data copied.

The working intranet v3.10.4 remains the customer-designated functional reference.
Its sanitized local copy has icon-related syntax damage and feature-code issues;
neither was repaired or treated as invalidating the deployed application. The
located Enhanced1 filename includes model, while the requested spelling uses mode.
Its target/features differ from the inspected Streamlit inference path. Artifact
lineage, runtime/class/horizon/eligibility alignment, physical SQL mappings and
sanitized working-intranet feature evidence remain unverified. No model loaded,
trained, executed or replaced; no SQL/network calls or dependency changes.

Documentation checks: exact five-file scope, relative links, UTF-8/plaintext,
trailing whitespace, empty index, unchanged application files and byte-preserved
FIS-001/FIS-002 decision text passed (exit 0). `git diff --check` passed (exit 0).
Both new untracked contracts were explicitly reviewed with the existing scanner's
Inspect-Text function plus plaintext/link/size checks: 2/2 files, zero leads,
exit 0. No scanner rules changed and neither file was staged.

`scripts/security_check.ps1` exited 0: 61 tracked/index files, zero confirmed
violations, 10 manual leads (five existing expressions in index and working tree).
All manual findings are dispositioned:

| Existing location (two leads each) | Disposition |
|---|---|
| api/config.py SecretStr declaration | No embedded credential |
| api/providers.py runtime server binding | Injected configuration; no embedded endpoint |
| api/providers.py runtime credential binding | Injected secret argument; no embedded value or logging |
| frontend/e2e/dashboard.spec.ts hostname comparison | Existing loopback assertion; heuristic match |
| PROJECT_STATE.md historical Playwright-option text | Existing benign server-reuse setting; heuristic match |

The scanner's REVIEW REQUIRED status denotes reviewed heuristic findings, not
confirmed violations. New documents contain no restricted SQL definitions,
addresses, real organizational mappings, operational records or model artifacts.
`scripts/verify.ps1 -PythonExecutable .venv/Scripts/python.exe` exited 0:
139 tests passed in 55.317 s; zero failures, errors or skips, including the
protected readiness regressions. Existing pandas/Starlette advisories remain
unsuppressed; no dependency changes were made. This verifies existing behavior,
not live SQL, Streamlit UI execution or model compatibility. The separate portable,
frontend and harness-scenario suites were not rerun for this documentation-only task.
Final staged Git/security checks and publication results are reported in the PR.
No application changes, SQL access, model execution, merge or deployment.


## PR #7 mobile chart touch-scroll correction - 2026-11-21

Focused fix branch `fix/history-mobile-touch-scroll` starts at merged PR #7,
`a269af932c062afe889ee8d0ff29a5e2458d5fb5`. The SVG's `touch-action: pan-y`
blocked horizontal touch panning inside `.chart-scroll`; changing only that value
to `auto` lets the browser scroll the existing overflow container. Chart handlers,
API contracts, backend, simulator, FIS-001/FIS-002 and dependency pins are unchanged.

A new Playwright regression enables touch input and sends Chromium DevTools
`Input.dispatchTouchEvent` start/move/end gestures over the SVG. It never assigns
scrollLeft or dispatches synthetic DOM events. The test failed on the old CSS
(exit 1, scrollLeft stayed 0), then passed with the fix: movement exceeds 60 px
in both themes; Home/ArrowRight/End inspection still works after the swipe.

Commands use existing installed dependencies, with frontend npm prefix
`npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache`.
`run check` passed; `test` passed 61/61; `run build` passed (19 modules).
`run test:e2e -- --project=history-desktop --project=history-tablet --project=history-mobile`
passed 13 tests in 49.2 s, with two intentional skips of the new mobile-only case
on desktop/tablet. All 12 existing history cases passed, covering hover/keyboard,
filters, errors and both themes. Six screenshots were regenerated as ignored
local artifacts. Installed Edge touch emulation is not physical-device/iOS evidence.

Root command `scripts/verify.ps1 -PythonExecutable .venv/Scripts/python.exe`
passed 139/139 in 65.454 s, zero failures/errors/skips, exit 0.
Recovered final harness evidence, confirmed for publication on 2026-11-22:
`tests/test_engineering_harness.ps1 -PythonExecutable .venv/Scripts/python.exe`
exited 0 with `HARNESS RESULT: PASS; Checks: 12`, including 134 passing portable
tests and five explicitly excluded external-reference tests. No successful test
suite was repeated during recovery or publication. Unaffected CSV browser projects
were not rerun for this fix.
`scripts/security_check.ps1` exited 0: 61 files, zero confirmed violations,
10 manual leads (five existing expressions duplicated across index/working tree).
All are benign: SecretStr declaration, runtime server and credential bindings,
loopback test comparison and the existing Playwright-option documentation match.
Scanner rules are unchanged. Git whitespace/protected-file checks pass; generated
screenshots, build output, caches and reports remain excluded from publication.
Every security lead is dispositioned below; each expression is reported twice,
once for the index and once for the working tree (10 leads total):

| Existing location | Disposition |
|---|---|
| `api/config.py` SecretStr field | Declaration only; no embedded credential |
| `api/providers.py` server binding | Runtime configuration argument; no embedded endpoint |
| `api/providers.py` credential binding | Injected secret argument; no embedded value or logging |
| `frontend/e2e/dashboard.spec.ts` hostname comparison | Loopback assertion; heuristic match |
| `docs/PROJECT_STATE.md` historical Playwright-option text | Benign test-server setting; heuristic suffix match |

Publication checks scan the staged index using the unchanged security script;
manual leads remain reviewed findings rather than confirmed violations.

## Phase 03B-2B Task 2 React historical dashboard review — 2026-11-21 (Asia/Dubai)

Branch `feature/phase03b2b-react-history`; clean starting HEAD
`726f34320c5ca658b70bd16b149b52dff3e724e5` contains the historical series API
merge through PR #6. This section supersedes earlier pending Task 1 publication
statuses; prior evidence is historical. No remote access was required. FIS-001,
FIS-002, all backend source/tests, simulator, readiness engine, Python pins and
frontend package.json/package-lock.json are unchanged.

### Implemented UI and data flow

Existing minimalist dashboard retained, now explicitly labelled fictional
helicopter history rather than live operational intelligence. Light theme defaults
to white/off-white/navy/teal; optional dark uses local CSS variables with identical
controls/data. No images, hero art, new animations, theme/chart library, CDN,
external font, analytics, storage persistence or authentication placeholder added.

The new HistoricalTrends component consumes validated API series for 30/90/180/365
days, with actual date axis, fixed 0..100 percentage axis, solid/dashed legend,
unsmoothed daily polylines, hover/focus details, Home/End/arrow keys, native day
slider and equivalent daily table. Both line paths preserve every observation.
The table includes PMC aggregate plus six canonical counts. It is memoized apart
from transient chart selection; paths are memoized per series. Narrow screens
scroll the plot/table within labelled focusable regions rather than the page.

Existing date/command/latest-snapshot controls remain intact; the historical
window persists across snapshot selection. The API-resolved snapshot date and
command are used consistently in series requests. Last-point metrics/status
counts must match the selected snapshot. No readiness formula is computed in
React: count reconciliation is validation; percentage coordinates/rounding are
presentation. Command comparisons now include API FMC/PMC/NMCS/NMCM/DEPOT counts;
the compact stacked composition and matching labels preserve PMCM/PMCS separately.

AbortController cleanup plus response guards prevent stale work from replacing
newer selections. Window changes clear obsolete charts immediately; valid snapshot
metrics remain available on history-only failures. CSV mode's exact synthetic
Not Found response is distinguished as unsupported history. Other empty, invalid,
malformed, unavailable and retry states remain explicit. SQL from health or later
history response blocks the demo and clears metrics; no fabricated fallback data.

The local React review skill checklist was applied: stable hook dependencies and
cleanup, parallel independent snapshot fetches, no remote/runtime fixtures, memoized
heavy table/path work, typed unknown-response validation, native accessible controls,
labels, focus visibility, keyboard chart/table access and no new dependencies.

### Actual executed checks

Frontend commands ran from C:\AI\Projects\FIS4\frontend; Python/harness/security
from the root. Existing Node 24.4.1 / npm 11.4.2 and project .venv were reused.
All recorded commands below exited **0**. No packages or browser binaries installed.

| Actual command / check | Recorded implementation result before final corrections |
|---|---|
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run check` | TypeScript PASS |
| Same npm prefix, `test` | **61/61 Vitest passed**, three files, 13.94 s; original 32 retained plus 29 new cases |
| Same npm prefix, `run build` | TypeScript/Vite PASS; 19 modules; local JS 243.16 kB, CSS 15.80 kB, HTML 0.57 kB |
| Same npm prefix, `run test:e2e` | **27/27 Playwright passed**, zero retries, 1.2 min; original 15 CSV tests plus 12 history tests |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **139 passed**, 0 failures/errors/skips, 66.322 s |
| Same verify command with `-TestMode Portable` | **134 passed**, 0 failures/errors/skips, 65.587 s; same five external-reference tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 checks passed**, unchanged harness and expectations |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 56 tracked files; exit 0; 0 confirmed violations; nine manual leads dispositioned below |
| Inline existing-scanner Inspect-Text AST extraction, exact five-file untracked inventory, plaintext/link/size and whitespace checks | **5/5 passed**, no additional leads; no index modifications |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code 726f343 -- AGENTS.md docs/DECISIONS.md readiness.py simulator api tests requirements.txt frontend/package.json frontend/package-lock.json` | Protected decisions, backend/engine/simulator/regressions and all dependency declarations unchanged |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | Final whitespace/scope checked; new-file whitespace reviewed separately |

Small loops: the original 32 frontend tests passed before extending coverage.
One new TypeScript selector initially used an unsupported Testing Library option;
it was corrected and all checks rerun. The first full history browser run passed
24/24. Adding explicit hover verification exposed a test assumption about the full
SVG midpoint being visible on mobile's scrollable plot; targeting a known visible
observation corrected the assertion. Final browser run adds real delayed-request
cancellation coverage and passes 27/27. No tests or security rules were weakened.
Line-ending-only noise in App.tsx and the original fixture was removed by preserving
their baseline line endings. Known pandas, Starlette/HTTPX, Vitest environment-startup
and Playwright NO_COLOR/FORCE_COLOR advisories remain non-blocking and unsuppressed.

### Actual browser integration and screenshot evidence

Playwright owns separate loopback CSV FastAPI/Vite (8000/5173) and fictional
history FastAPI/Vite (8001/5174) servers; reuseExistingServer=false. The existing
cache is initialized normally through lifespan in the test/demo helper; no SQL
connection is made. All browser page requests are restricted/asserted loopback.
Tests compare actual API percentages to rendered line coordinates, check every
window, date/command/latest reset, six statuses/table, hover and keyboard controls,
CSV unsupported mode, malformed/unavailable history, SQL blocking and actual
request cancellation with a delayed obsolete response. Component tests additionally
cover late responses even when mocked transport ignores abort.

CSV viewports remain 1440x1000, 768x1024 and 1024x768. History viewports are
1440x1000, 768x1024 and 390x844. Both themes are tested for document overflow and
sampled text contrast >=4.5 at heading, KPI, selected-source badge and day detail;
this is not a full accessibility audit. Final light/dark desktop and dark tablet/
mobile screenshots were visually inspected, along with earlier light mobile.
No claim of matching an unavailable approved design reference is made.

Six actual final PNGs are generated under ignored frontend/test-results folders:

| View | Directory suffix under frontend/test-results | Files |
|---|---|---|
| Desktop | history-real-history-value-469d1--and-responsive-screenshots-history-desktop | history-light.png, history-dark.png |
| Tablet | history-real-history-value-469d1--and-responsive-screenshots-history-tablet | history-light.png, history-dark.png |
| Mobile | history-real-history-value-469d1--and-responsive-screenshots-history-mobile | history-light.png, history-dark.png |

Generated screenshots/reports/dist/node_modules/caches remain ignored. No server
is published; test-owned server cleanup and port status are checked at completion.
The build contains local compiled assets only; it is not FIS-002 release packaging.
All fifteen exact direct pins and the existing lockfile remain unchanged. Lockfile
SHA-256: `8f2a864278789887a3be38933447a92f47156cd560e887796f6ca8c5f4416ccb`.

### Security dispositions, inventory and remaining risks

The first eight tracked leads are the same four expressions in index and working copy:
api/config.py:30 is a SecretStr declaration without a credential value;
api/providers.py:86 binds a runtime server argument without an embedded endpoint;
api/providers.py:89 binds an injected SecretStr without embedded value/logging;
frontend/e2e/dashboard.spec.ts:14 compares hostname to loopback values and is a
heuristic match. The ninth lead is docs/PROJECT_STATE.md, working tree line 82,
under database-endpoint-assignment. Its cause is the Playwright option spelling
on that line: the heuristic matches the suffix of the option name before the
equals sign. This documents disabling reuse of existing test servers, not a SQL
endpoint or credential. Disposition: benign test-configuration documentation;
retain the evidence and scanner rules unchanged. All nine are explicitly resolved,
with zero confirmed violations or unresolved manual findings. Five new
frontend/test files have zero extra leads.
Scanner rules are unchanged; future approved staging still needs a post-staging
scan. This is not a vulnerability-database or full-history audit.

Changed frontend files: playwright.config.ts; vite.config.ts; src/App.tsx;
src/ReadinessPanels.tsx; src/api.ts; src/styles.css; src/tokens.css;
src/test/fixtures.ts; src/HistoricalTrends.tsx; src/history.test.tsx;
src/test/historyFixtures.ts; e2e/history.spec.ts; e2e/history_backend.py.
Documentation: README.md, docs/HISTORY_API.md, docs/PROJECT_STATE.md,
docs/RELEASE_GATES.md and docs/TASKS.md. Eighteen files total, all left unstaged.

### Final corrections after recovery audit

Only three existing task files changed in this follow-up: src/styles.css under
frontend, this PROJECT_STATE and RELEASE_GATES. The CSS change is one dark-only
rule selecting native appearance and removing the dark custom background image.
The existing dark color scheme supplies a legible native select chevron; light
selectors and dashboard logic/contracts remain unchanged. No refactor or new
feature was introduced. The ninth scanner disposition above corrects the earlier
eight-lead documentation without removing evidence or modifying scanner rules.

Fresh executed checks, each exit 0:

| Actual follow-up command/check | Actual result |
|---|---|
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run build` from frontend | TypeScript/Vite PASS; 19 modules; JS 243.16 kB, CSS 15.87 kB, HTML 0.57 kB |
| Same npm prefix, `run test:e2e -- --project=history-desktop --project=history-tablet --project=history-mobile --grep "real history values"` | **3/3 affected browser cases passed**, 43.6 s, no retries; both themes exercised in each case |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | Mandatory final engineering gate: **139 passed**, 0 failures/errors/skips, 67.937 s |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | **56 tracked files**, 0 confirmed violations, **9 manual leads**, all dispositioned; REVIEW REQUIRED, exit 0 |
| Final screenshot freshness/ignore/port checks | **6/6 PNGs regenerated after final CSS**, all ignored; 8000/8001/5173/5174 free |

The final CSS write was 13:45:32 UTC on 2026-11-21; screenshots were regenerated
13:46:11..13:46:19 UTC. Thus all six (light/dark desktop, tablet and mobile)
reflect final application source. New dark desktop/mobile screenshots were also
visually inspected and show the native light chevrons clearly. Screenshot paths
are unchanged in the table above. The unaffected 61 Vitest, full 27 Playwright,
134 portable and 12 harness results are retained prior evidence, not newly claimed
reruns in this CSS-only follow-up. Final source/decision/pin and whitespace/index
checks remain mandatory, with no staging or publication authorized.

Deferred: authentication/authorization; full accessibility/assistive-technology
audit; independent customer design validation; production load/TLS/multi-worker
and actual SQL acceptance; FastAPI static asset serving; FIS-002 clean isolated
offline release/package/rollback acceptance; helicopter imagery; ML/prediction,
maintenance drilldowns and cloud deployment. Mobile plot/table use local scrolling;
theme preference resets per session. Unsupported-history detection relies on the
existing synthetic 404 convention, not a new capability endpoint. No packages,
operational data, SQL, source security settings, training, forecast or deployment
were introduced. No commit, push, merge, staging or packaging was performed.

## Phase 03B-2B Task 1 historical series review — 2026-11-21 (Asia/Dubai)

Branch: `feature/phase03b2b-history-dashboard`; clean starting HEAD:
`9ac0f9aa7fc3243438363113ce920469344f3b8f`, Phase 03B-2A merged through PR #5.
No remote query was required. This section supersedes older pending Phase 03B-2A
publication statuses; earlier evidence remains historical. FIS-001/FIS-002,
readiness engine, simulator algorithm, original Python regression tests, provider
configuration/SQL implementation, dependencies and frontend are unchanged.

### Implemented behavior and reviewed scope

New `GET /api/v1/readiness/history/series` is registered only for explicitly
selected synthetic_history mode. It requires end_date and a canonical days value
30/90/180/365, with optional provider-allowlisted command. End is inclusive and
must be within history; start clips to available history. Effective start/end,
requested window and actual point count are returned. Each chronological daily
observation contains existing Metrics plus six canonical status counts preserving
PMCM/PMCS separately. Counts and percentages reference existing frozen records;
no readiness formula, generation, snapshots, pandas aggregation or event loading
is performed in requests. The range reader captures one consistent immutable
cache reference, performs at most 365 lookups and retains no new cache entries.

New response models bound observations/point_count to 1..365, and canonical counts
to 0..160. The validated response is serialized once; its actual uncompressed JSON
body is capped at **262,144 bytes (256 KiB)**. Overflow returns generic 500, never
truncated data. Required/malformed/unknown/duplicate query values return safe 422,
out-of-history end returns 404, absent/closed/internally incomplete cache returns
503 with no partial series. Existing error/source conventions are reused.
Default CSV and SQL providers do not expose the route or initialize synthetic
history. All existing endpoint implementations/contracts remain unchanged.

Exact API/model/error conventions and examples are appended to HISTORY_API.md.
Reviewed files: api/history.py; api/main.py; tests/test_history_series.py;
scripts/benchmark_history_series.py; tests/test_engineering_harness.ps1;
docs/HISTORY_API.md; docs/PROJECT_STATE.md; docs/RELEASE_GATES.md; docs/TASKS.md.
Only expected totals/labels change in the engineering harness; its original
twelve scenarios and security rules are retained. No frontend work was started.

### Executed verification

Existing FIS4 .venv / CPython 3.13.7 Windows x64 and exact requirements pins were
reused, without packages, internet, operational data or SQL access. Commands ran
from C:\AI\Projects\FIS4. Completed checks below exited **0**. Existing pandas
inference and Starlette HTTPX adapter advisories remain non-blocking; no package
changes or warning suppression were introduced.
Local importlib.metadata confirmed FastAPI 0.164.0, Pydantic 2.14.3,
pandas 2.3.3, NumPy 2.3.4, HTTPX 0.28.1 and Uvicorn 0.54.0; no versions changed.

| Actual command / check | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_history_series.py -v` | **19/19 passed**, 17.458 s |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **139 passed**, 0 failures/errors/skips, 59.824 s; all original 120 plus 19 new series tests |
| Same verify command with `-TestMode Portable` | **134 passed**, 0 failures/errors/skips, 58.894 s; same five external legacy-reference tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 passed**; all original scenarios preserved, counts extended to 139/134 |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 54 tracked files; 0 confirmed violations; eight existing reviewed leads; REVIEW REQUIRED, exit 0 |
| Inline existing-scanner Inspect-Text AST extraction, exact two-file untracked allowlist, link/size/plaintext and trailing-whitespace checks | Both new files scanned, 0 manual leads; exit 0; no index modifications |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code 9ac0f9a -- AGENTS.md docs/DECISIONS.md readiness.py simulator api/config.py api/providers.py tests/test_readiness.py tests/test_api.py tests/test_providers.py tests/test_history_api.py tests/test_simulator.py tests/legacy_reference.py tests/suite_selection.py scripts/verify.ps1 scripts/security_check.ps1 requirements.txt frontend data/synthetic_readiness.csv TEST_REPORT.md` | All protected decisions/logic, original regressions, default/SQL paths, frontend and dependencies unchanged |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | PASS; untracked file whitespace checked separately |

Nineteen tests cover all windows, inclusive/clipped boundaries, every-day fleet/
command reconciliation for every window, exact cached metrics and FIS-001 (NMCM
retained), separate six-status counts, strict and duplicate/encoded query keys,
default/SQL/override isolation, unavailable/incomplete cache, immutable results,
concurrent/repeated reads, schema/read-only behavior and exact payload-limit
boundaries. Warm tests patch simulator generation, preparation, event loading,
readiness snapshot/metric functions and DataFrame.groupby to fail on invocation.
One real validated full world is prepared for the series test module; individual
tests use defensive copies of its existing immutable-cache fixture.

### Measured warm response sizes and timings

Actual command, exit 0:

```powershell
.\.venv\Scripts\python.exe -B scripts\benchmark_history_series.py --requests 30
```

Real history-mode lifespan initialization ran once, separately measured **18.422 s**
(clock starts after app construction/imports). It is excluded from warm timings.
As-of 2026-11-20, seed 42017; one untimed request per selection followed by 30
sequential timed requests per row (240 total). Body sizes were identical across
repetitions of each selection; exact UTF-8 JSON bytes, excluding headers:

| Days / points | Command | Body bytes | Mean ms | Median ms | Min..max ms |
|---:|---|---:|---:|---:|---:|
| 30 | fleet | 7,227 | 4.160 | 3.853 | 3.248..6.581 |
| 30 | FICTIONAL_A | 7,028 | 10.684 | 9.715 | 3.378..27.495 |
| 90 | fleet | 21,422 | 16.273 | 13.523 | 8.960..43.920 |
| 90 | FICTIONAL_A | 20,787 | 12.577 | 9.865 | 4.794..31.338 |
| 180 | fleet | 42,837 | 11.055 | 10.784 | 6.697..17.792 |
| 180 | FICTIONAL_A | 41,191 | 10.186 | 8.923 | 6.269..44.297 |
| 365 | fleet | 86,839 | 10.334 | 10.126 | 7.379..15.983 |
| 365 | FICTIONAL_A | 83,539 | 14.480 | 12.225 | 7.895..27.142 |

These are local in-process TestClient/ASGI/thread dispatch/validation/JSON timings,
with normal host/scheduling variability, not monotonic size-to-latency guarantees.
They do not measure TCP/TLS, external clients, production authorization, concurrent
load or multi-worker deployment. No new memory/RSS benchmark was performed in
this task. Request work and payload have explicit bounds; prior initialization
memory measurements above/below are historical evidence, not new results.

### Security disposition and stop boundary

The eight tracked manual leads are four expressions in index and working tree:
api/config.py:30 declares SecretStr without an embedded credential;
api/providers.py:86 binds a runtime server argument without an embedded endpoint;
api/providers.py:89 binds injected SecretStr without embedded value/logging;
frontend/e2e/dashboard.spec.ts:14 checks loopback hostname equality, a heuristic
match. All eight are explicitly resolved; there are no confirmed violations or
unresolved manual findings. The two new test/benchmark files have zero additional
leads under unchanged text rules. Scanner policy is unchanged. Future staging
still requires an index/working-tree scan; no vulnerability-database or full Git
history audit is claimed.

Remaining risks: authentication/authorization absent, real network/concurrent-load/
TLS/multi-worker capacity unverified, per-worker cold generation/cache lifecycle
and FIS-002 isolated offline release acceptance deferred. No SQL access, external
services, packages, ML/prediction, simulator changes, frontend, deployment or
packaging was introduced. All nine reviewed files remain **unstaged**; no commit,
push or merge. Proposed commit: `FIS4 Phase 03B-2B Task 1: bounded historical trend API`.

## Phase 03B-2A historical API local review — 2026-11-21 (Asia/Dubai)

Branch `feature/phase03b2-history-api` starts clean at
`37c8120f5d6c08a6650f94141a71faf156784d16`, the locally verified Phase 03B-1
simulator merge through PR #4. This section supersedes prior simulator publication
and proposal-only API statuses; earlier records are retained as historical evidence.
No remote access was needed. No simulator algorithm, FIS-001/FIS-002 text,
readiness implementation, baseline Python tests, frontend or dependencies changed.

### Implemented architecture and contracts

Explicit `synthetic_history` provider mode requires validated history.as_of and
optional strict seed (default 42017), with fixed 160 tails/four commands/four years.
History and SQL settings cannot be mixed; both synthetic modes reject credentials
or a connector. Default remains the original small CSV fixture. The new
`GET /api/v1/readiness/history?date=YYYY-MM-DD[&command=FICTIONAL_A]` is registered
only in history mode, reusing FleetResponse and existing safe-error conventions.
Required/invalid dates, unknown/duplicate keys and invalid/unknown commands return
422; dates outside history return 404. Source/header remain synthetic. CSV/SQL
applications do not register/expose this route and do not initialize history.

FastAPI lifespan initializes one per-app cache in a worker thread. A lock
serializes initialization and atomically publishes immutable records. One real
simulator world is generated/validated; the original daily metric function is
called for fleet and each command subset during preparation. There are five
records per day (7,305 in the example), with six canonical status counts. Large
snapshot/telemetry/episode/action frames are released; private events are retained
only for the defensive-copy DataProvider contract. No global/client-keyed cache.

Existing aggregate endpoints preserve their contracts and default/SQL paths.
When history is explicitly selected they use cached records instead of snapshot
reconstruction or aggregation. Failure publishes no partial data, fails startup
with generic HistoryUnavailable, and is sticky for that provider; no fixture
fallback or request retry. Missing lifecycle/cache gives safe 503. Shutdown clears
the cache; a fresh successful lifespan prepares once again. SQL logic/bounds and
no-fallback safeguards are unchanged. `/health` is still liveness only.

Provider contract, exact validation/status conventions, startup and example
requests are documented in `HISTORY_API.md`. Authentication/authorization is not
implemented and is not claimed by the new route; localhost demonstration remains
separate from production access-control acceptance.

### Executed verification evidence

Existing FIS4 .venv, CPython 3.13.7 Windows x64, pandas 2.3.3 / NumPy 2.3.4,
and the existing exact requirements pins were reused. No new packages/downloads,
real SQL, external services or operational records. Commands run from FIS4.
All completed checks below exited **0**; known pandas date-inference and
Starlette TestClient/HTTPX adapter advisories remain non-blocking. No package
installation or warning suppression was used.

| Actual command / check | Result |
|---|---|
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_history_api.py -v` | 22/22 new tests passed; initial 14.368 s, final strengthened concurrency suite 13.744 s |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **120 passed**, 0 failures/errors/skips, 35.635 s; all original 98 plus 22 history tests |
| Same verify command with `-TestMode Portable` | **115 passed**, 0 failures/errors/skips, 34.956 s; same five external legacy-reference tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 passed**; all original scenarios retained, counts extended to 120/115 |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 50 tracked files; exit 0; 0 confirmed violations; 8 existing manual leads dispositioned below |
| Inline existing-scanner Inspect-Text AST extraction, exact untracked-file allowlist and plaintext/size/link checks | **4/4 new files scanned**, 0 manual leads; whitespace check passed; no staging |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code 37c8120 -- AGENTS.md docs/DECISIONS.md readiness.py simulator tests/test_readiness.py tests/test_api.py tests/test_providers.py tests/test_simulator.py tests/legacy_reference.py tests/suite_selection.py data/synthetic_readiness.csv requirements.txt frontend TEST_REPORT.md` | Protected decisions/formulas, simulator algorithm/regressions, API baseline tests, dependencies and React unchanged |

The tests cover default provider/OpenAPI preservation, exact population/date
coverage, three-date fleet/command reconciliation, independent original-engine
metric comparison with NMCM retained, strict date/command/query validation, single
initialization, no warm generation/snapshot/aggregation, concurrent initialization
and HTTP reads, read-only results, instance/config/shutdown isolation, restart,
sticky safe initialization failure, missing lifespan, SQL isolation and provider
override rejection. Full real data is prepared once per test suite; lifecycle
tests clone immutable cache fixtures. Benchmarks below use real app generation.
The final concurrency test additionally coordinates eight threads with a barrier
and a blocked preparation event; all 22 history tests were rerun successfully
after this test-only strengthening. A supplemental inline whitespace check first
used a PowerShell-quoted character class incorrectly; its regex was corrected and
the full untracked scan/check rerun successfully, without changing source content
or weakening scanner rules.

### Measured performance and memory

Actual commands, both exit 0:

```powershell
.\.venv\Scripts\python.exe -B scripts\benchmark_history.py --requests 30
.\.venv\Scripts\python.exe -B scripts\benchmark_history.py --requests 30 --profile
```

As-of 2026-11-20 / seed 42017: **13.299 s** cold construction/lifespan initialization
including generation, validation and aggregate preparation. This excludes earlier
interpreter/API imports. Warm in-process TestClient requests (30 per row, 180 total):

| Historical date | Command | Mean ms | Median ms | Min..max ms |
|---|---|---:|---:|---:|
| 2022-11-21 | fleet | 4.078 | 3.695 | 3.021..7.713 |
| 2022-11-21 | FICTIONAL_A | 5.751 | 5.442 | 3.873..12.093 |
| 2024-11-20 | fleet | 7.931 | 7.487 | 3.113..14.730 |
| 2024-11-20 | FICTIONAL_A | 4.624 | 3.769 | 2.844..10.126 |
| 2026-11-20 | fleet | 4.520 | 3.833 | 2.793..9.032 |
| 2026-11-20 | FICTIONAL_A | 3.289 | 3.135 | 2.596..5.695 |

Separate tracemalloc run: **6,277,108 bytes retained (5.99 MiB)** after startup/GC,
**185,198,043 bytes peak (176.62 MiB)**, including lazy simulator imports and other
retained Python state. Profiled cold time **68.767 s** includes instrumentation
overhead and is not the normal cold latency. Tracing was stopped before its warm
requests. These are Python allocations, not OS RSS/working set or all native
allocations. Warm measurements include ASGI/TestClient/thread/JSON overhead,
not real TCP/TLS, access control, multi-worker or production load acceptance.

### Security dispositions and deferred risks

The scanner's eight leads represent four expressions in index and working copy:
api/config.py:29 (index)/30 (working tree) declares SecretStr without a credential;
api/providers.py:86 binds a runtime server argument without an embedded endpoint;
api/providers.py:89 binds an injected SecretStr without embedded value/logging;
frontend/e2e/dashboard.spec.ts:14 checks loopback hostname equality, a heuristic
match. All are reviewed and resolved. No confirmed violations; scanner rules
unchanged. New code has no secret/config discovery, external calls, live SQL,
model use, persisted data or runtime CDN. Untracked files are explicitly scanned
with existing text rules because the mandatory tracked scan excludes them.
Post-staging scanning remains necessary if staging is later approved.

Deferred: authentication/authorization, real socket/load/TLS and multi-worker
startup/aggregate memory measurements, durable artifact loading instead of cold
generation, production startup budgets, real SQL integration and FIS-002 clean
isolated offline packaging/transfer acceptance. Each worker prepares its own
bounded cache; no cross-process sharing, refresh or on-disk cache is implemented.
The simulator's fictional assumptions remain uncalibrated; no ML/inference,
prediction score/forecast endpoint, deployment or cloud work was introduced.

All changes remain **unstaged**, with no commit, push, merge or deployment.
Reviewed files: README.md; api/config.py; api/main.py; api/providers.py;
api/history.py; docs/HISTORY_API.md; docs/PROJECT_STATE.md; docs/RELEASE_GATES.md;
docs/SIMULATOR.md; docs/TASKS.md; scripts/benchmark_history.py;
tests/test_engineering_harness.ps1; tests/test_history_api.py.
Proposed commit: `FIS4 Phase 03B-2A: cached historical readiness API`.

## Phase 03B Task 1 implementation review — 2026-11-20 (Asia/Dubai)

Branch: `feature/phase03b-fleet-simulator`; starting HEAD and local main:
`25b1eaa5e8e464247d9b49e38c468d0aa03b9dd3`, merged Phase 03A PR #3.
The supplied baseline has 45 characters, with an extra `dcfad` suffix after this
valid 40-character Git SHA. Local main and branch match the valid prefix; no
fetch or branch rewrite was needed. This section supersedes pending Phase 03A
publication/authorization statuses below; earlier evidence remains historical.
FIS-001/FIS-002 and protected readiness/API/frontend files are unchanged.

### Implementation

New `simulator/` package separates validated contracts, persistent episode
generation and optional local measurement/CSV export. Defaults: 160 zero-padded
fictional tails, four balanced commands, seed 42017, four calendar years, explicit
as-of date. Bounded configuration supports other balanced sizes/date ranges.

Normalized aircraft, readiness events, daily operations, maintenance/depot episodes
and supply/lifecycle actions feed daily snapshots using the original engine.
Persistent major/minor faults, recurring families, supply wait/receipt/repair,
inspection consumption/resets and staggered depot entry/exit govern daily flight
opportunities. Invented command stress/tempo/delays introduce imperfect effects.
`features_at(day)` uses only end-of-day observed state for strictly later targets;
it never reads eventual closes, future actions or latent sampled durations.
The history structurally implements DataProvider (`source`, defensive load_events)
but is deliberately not selected or imported by the API.

Nineteen portable simulator tests added. All twelve original harness scenarios
retained with expected counts updated; no existing regression expectation or
scanner rule changed. The first loop's test-only pandas chained-assignment warning
was corrected by binding the target frame before mutation. Explicit schemas,
fictional assumptions, time/CSV/SQL contracts, censoring/leakage boundaries and
future cached API strategy are documented in `SIMULATOR.md`.

### Actual executed verification

Commands ran within FIS4 using existing CPython 3.13.7 Windows x64, pandas 2.3.3,
NumPy 2.3.4. No downloads/new packages. Every completed command below exited **0**.
Sandbox process setup failed; scoped authorized execution was used without Full
Access or security-setting changes.

| Actual command/check | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_simulator.py -v` | Initial loop 19/19 passed; later final full/portable suites also pass all 19 |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **98 passed**, 0 failures/errors/skips, 24.715 s: original 79 plus 19 simulator tests |
| Same verify command with `-TestMode Portable` | **93 passed**, 0 failures/errors/skips, 23.492 s; same five external-reference tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 passed**, preserving full/automatic/portable and original failure/redaction scenarios |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 44 tracked files; 0 violations; same 8 resolved manual leads; REVIEW REQUIRED, exit 0 |
| Inline PowerShell: parse existing scanner AST, extract Inspect-Text, exact six-file untracked allowlist, plaintext/size/link checks and unchanged scanner text rules | 6 new files scanned, 0 additional leads; no index changes |
| `.\.venv\Scripts\python.exe -B -m simulator --as-of 2024-02-29 --seed 6303 --tails 8 --years 1 --export` | 8 tails/four commands/366 days; 2,928 daily rows; six CSVs plus manifest in ignored workspace folder |
| Inline Python CSV readback: six manifest SHA-256 checks, text tail dtype, explicit timestamp parsing, original-engine snapshot comparison | PASS; leading-zero `000001` and snapshot parity retained |
| `.\.venv\Scripts\python.exe -B -m simulator --as-of 2026-11-20` | Default full dataset validated; final normal measured run **7.953 s** |
| Same generation command with `--profile` | Python allocation profile; details below |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code 25b1eaa -- AGENTS.md docs/DECISIONS.md readiness.py api frontend requirements.txt tests/test_readiness.py tests/test_api.py tests/test_providers.py tests/legacy_reference.py tests/suite_selection.py data/synthetic_readiness.csv TEST_REPORT.md` | Protected decisions/engine/tests, API/React, fixture and dependencies unchanged |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | PASS; new untracked files separately reviewed |

Tests verify exact population/coverage, identical repeated full tables/bytes,
different valid seed, canonical statuses, ordering/conflicts, engine reuse and
fleet/command reconciliation, hours/inspection accounting, persistent causal
supply/depot/maintenance lifecycles, future-outcome exclusion, private RNG state
and rejection of corrupted coverage/timing/counters/hours/statuses.

Default as-of 2026-11-20 covers 2022-11-21..2026-11-20: **1,461 days**.
Aircraft 160; readiness events 10,273; daily operations 233,760; episodes 4,351;
actions 11,564; daily snapshot 233,760. All six canonical statuses occur.
Deep retained DataFrame memory: **87,235,837 bytes (83.19 MiB)**, including
object-column accounting which can double-count shared strings; this is not RSS.
Tracemalloc excludes untracked native allocations, interpreter/import startup
and OS overhead; profiling adds substantial time overhead. Maximum-size
configurations have not been benchmarked.

### Security dispositions and acceptance boundary

Eight tracked scan leads are four lines seen in both index and working tree:
api/config.py:29 is a SecretStr field declaration with no value;
api/providers.py:86 binds a runtime server argument with no embedded endpoint;
api/providers.py:89 binds an injected SecretStr with no embedded credential or
logging; frontend/e2e/dashboard.spec.ts:14 checks hostname equality against
loopback values, a heuristic match. All eight are explicitly resolved by source
review. The six new files have no additional leads. No confirmed violations or
unresolved manual findings. Scanner rules and actual Git index are unchanged;
post-staging scanning remains mandatory if later staging is approved. This is
not a vulnerability-database audit or full-history scan.

Limits: fictional, single-episode, daily-resolution assumptions; one spare demand
per fault; fixed commands; no overlapping faults/transfers. No physical/statistical
calibration, target construction, prediction usefulness or ML validation. The
validator independently rebuilds snapshots during preparation; nothing runs on
dashboard requests. Future integration should prepare/version once and cache/index
snapshots and original-engine aggregates while preserving API/provider bounds.
No SQL, operational data, credentials, legacy edits, API/React changes, external
access, cloud hosting, prediction endpoints or release packaging were used.

Changes remain **unstaged** for review; no commit, push or PR performed.
Proposed commit: `FIS4 Phase 03B Task 1: reproducible synthetic fleet history`.

## Current Phase 03A final staged review — 2026-11-20 (Asia/Dubai)

Branch: `feature/phase03a-react-dashboard`. HEAD remains
`8bd2ba87f52ed23574d6fb44e9cd5f74b4a219b4`, the separate FIS-002 documentation
commit. That commit, AGENTS.md and DECISIONS.md are preserved unchanged. This
review authorizes staging Phase 03A only; no commit, push, merge or simulator work
is authorized or performed. Earlier phase records below are historical evidence.
Local history contains Phase 02B as `c598ec4`; its earlier pending-publication
status is superseded by that local evidence, with no fresh remote query here.

### Scope and source review

Frontend source/configuration/tests, package.json, package-lock.json and the
single-line `src/vite-env.d.ts` Vite-client type reference were reviewed. Runtime
React modules import no test fixture and implement no readiness calculation.
Percentages/counts are API-owned; formatting is presentation only. A test confirms
the frontend displays API percentages even when counts would suggest other values.
API calls use fixed relative paths, credentials: omit and redirect: error; no
arbitrary API host, credential field, browser storage, unsafe HTML or runtime CDN
dependency is used. CSS has only a relative token import, installed system fonts
and an inline SVG data URI; its XML namespace is not a network asset request.

The flow is browser snapshot/command selection -> localhost Vite proxy -> existing
FastAPI synthetic provider/readiness engine -> validated responses -> rendered
KPIs/counts/commands/statuses. Health is checked before aggregate requests. SQL
health is labelled SQL and blocks aggregates. Missing/malformed/source-mismatched
data is not replaced with fabricated metrics. Responses are pinned to one API date;
cancelled or stale loads cannot overwrite the selected view. Source reporting
remains SQL if a late parallel synthetic response follows a SQL error.

Vite development binds 127.0.0.1:5173 and proxies /health and /api only to
127.0.0.1:8000; preview also binds loopback. No backend CORS/security changes are
required. Backend source, readiness.py, original tests, fixture and Python pins
are unchanged. FIS-001 formulas/regressions remain locked; FIS-002 remains binding.

No approved dashboard design references were found in the workspace. Design-reference
validation remains pending; no visual matching is claimed. Fresh desktop/tablet
screenshots were inspected. Browser tests verify responsive columns, no horizontal
overflow, keyboard/skip navigation, touch-sized controls and sampled contrast >=4.5.

### Dependency and generated-file review

Node 24.4.1 / npm 11.4.2. All 15 direct dependencies are exact pins and match
installed packages: React/React DOM 19.3.1; TypeScript 7.0.2; Vite 8.3.8; React
plugin 6.3.0; Vitest 5.1.1; jsdom 28.1.0; Playwright Test 1.65.1; Testing Library
DOM 10.4.2 / React 16.3.3 / user-event 14.6.13 / jest-dom 8.0.0; Node types
24.19.2 and React/React DOM types 19.3.0. No dependencies were installed or upgraded
during this review; npm checks used offline mode and a workspace-local cache.

package-lock.json is lockfileVersion 3, 88,681 bytes, with 169 resolved non-root
package entries. Root declarations match package.json; every entry has a version
and integrity record and an HTTPS registry.npmjs.org URL without embedded userinfo
or linked/local dependencies. Reviewed lockfile SHA-256:
`8f2a864278789887a3be38933447a92f47156cd560e887796f6ca8c5f4416ccb`.
This is a local lock/installation consistency review, not a vulnerability-database
audit or a claim of clean isolated release reproducibility.

check-ignore verified node_modules, dist, Playwright test-results/reports,
node_modules/.vite caches, workspace .harness-test-tmp and *.tsbuildinfo are
excluded. Only reviewed source, configuration, tests and the dependency lockfile
are proposed; no generated bundle, screenshot, browser binary, dependency tree,
cache, temporary fixture, environment file or credential is included.

### Fresh executed verification

The user supplied matching successful verification results before this review.
The commands below were independently rerun here. Frontend commands ran from
C:\AI\Projects\FIS4\frontend; backend commands ran from the repository root.
Every completed check listed exited **0**.

| Actual command/check | Actual result |
|---|---|
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run check` | TypeScript check PASS |
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache test` | Vitest **32/32 passed**, 2 test files, no failures/skips |
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run build` | TypeScript + Vite PASS; 18 modules; local JS 234.21 kB, CSS 11.51 kB, HTML 0.57 kB |
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run test:e2e` | Playwright **15/15 passed**, no retries; desktop 1440x1000, tablet portrait 768x1024, tablet landscape 1024x768 |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | Backend **79 passed**, 0 failures/errors/skips |
| Same backend verify command with `-TestMode Portable` | Backend **74 passed**, 0 failures/errors/skips; five external legacy-reference tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 harness checks passed**, original scenarios retained |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1 -RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\phase03a-proposed-review` | 44 reviewed proposed files; 0 violations; 8 manual leads, dispositioned below; REVIEW REQUIRED, exit 0 |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | Actual post-staging scan: 44 index/working-tree files; 0 violations; same 8 resolved leads; REVIEW REQUIRED, exit 0; repeated after final documentation staging |
| `git -c safe.directory=C:/AI/Projects/FIS4 check-ignore -v` with the reviewed generated-path allowlist | All 7 representative dependency/build/report/cache/temp paths ignored |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | No whitespace errors |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --cached --check` | Initial staged check found CRLF treated as trailing whitespace in the Vite-client declaration; normalized that one line to LF without changing its declaration; final staged check repeated before completion |
| `npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache --prefix frontend run check` from repository root | Post-line-ending TypeScript verification PASS, exit 0; no application logic or dependency change |
| Inline local Node checks of package/lock/installed versions and built HTML assets | All 15 pins/169 resolved lock entries valid; compiled HTML references local JS/CSS only; test-private markers absent from JS bundle |

Frontend browser tests start owned default-synthetic FastAPI and Vite servers on
loopback and use preinstalled Microsoft Edge. Tests compare rendered metrics with
actual API values, apply date/command filters, recover from 404/network errors,
check 422 and SQL health states, and assert no external page requests. SQL health
and failure cases are intercepted fictional responses; no SQL Server connection
is tested. The live FastAPI synthetic integration passed. Test-owned servers were
stopped afterward; both ports were free. No public server was exposed.

### Security dispositions and staged scope

The 26 tracked files plus the exact 18-file frontend source allowlist were copied
to a disposable workspace index for pre-staging review. Its exact cleanup path
was checked before removal. Every proposed source and the lockfile were covered.
The scanner's eight findings represent four code lines, each reported for index
and working-tree content:

| Location / rule | Explicit disposition |
|---|---|
| api/config.py:29, credential-assignment (2) | Existing SecretStr field declaration; no embedded credential value |
| api/providers.py:86, database-endpoint-assignment (2) | Existing runtime server argument binding; no embedded endpoint |
| api/providers.py:89, credential-assignment (2) | Existing injected SecretStr argument binding; no embedded credential or logging |
| frontend/e2e/dashboard.spec.ts:14, database-endpoint-assignment (2) | Test compares url.hostname to localhost/127.0.0.1; equality expression matched heuristically, not a DB endpoint assignment |

All eight leads are resolved by source review; there are no confirmed violations
or unresolved manual security findings. Scanner rules were not weakened. The
actual staged index/working-tree scan returned the same eight reviewed leads.
Final documentation is restaged and security checked before completing review.
Heuristic scanning does not inspect full
Git history or prove dependency vulnerability absence.

Reviewed Phase 03A stage list (23 files): .gitignore; README.md; docs/PROJECT_STATE.md;
docs/TASKS.md; docs/RELEASE_GATES.md; and all 18 reviewed frontend source/config/
test/lock files listed by the final staged inventory. AGENTS.md and DECISIONS.md
are excluded; their FIS-002 commit remains intact. No backend/Python file is staged.
The exact staged filename allowlist, staged whitespace and working-tree/index
consistency checks are repeated before completion. Generated files remain excluded.
After the successful checks, review documentation was updated and the single-line
Vite type declaration was normalized from CRLF to LF to satisfy the staged
whitespace check. Its declaration semantics are unchanged and TypeScript is rerun.
Application/test/lock logic remains the verified snapshot. HEAD stays at the
FIS-002 commit; no new commit is created.

### Limitations and stop boundary

Design-reference validation is pending. Authentication, real SQL Server integration,
cloud hosting, production static serving and offline release acceptance remain
unimplemented/unverified or separately gated. The local Vite build verifies compiled
assets, not FIS-002 clean isolated Windows ZIP acceptance. Future FastAPI static
asset serving must preserve the API routes and require no Node.js on the intranet.
No synthetic fleet simulator, Phase 03B, ML or release-packaging work was started.
Existing pandas inference and Starlette HTTPX adapter warnings remain; Vitest emits
an environment-startup performance advisory and Playwright emits NO_COLOR/FORCE_COLOR
advisories. These are non-blocking and not suppressed by application changes.

Proposed commit: `FIS4 Phase 03A: React readiness dashboard`.
Stop at final staged review; commit/push/merge require explicit later approval.

## Historical Phase 02B records

## Current Phase 02B record — 2026-11-19 (Asia/Dubai)

Branch verified: `feature/phase02b-sql-provider`, initially clean. Local HEAD is
`d9d8ffa` (Merge pull request #1 from arbindchristy/feature/phase02-fastapi).
This local history supersedes the old Phase 02A awaiting-publication statements
in the historical records below; no fresh remote inspection occurred in Phase 02B.
No staging, commit, push or merge was performed at the implementation handoff.
The subsequent review task authorizes staging reviewed Phase 02B files only;
commit, push and merge still require explicit approval.
Result: **PASS at the mocked-provider acceptance gate**; real SQL integration
remains unaccepted and untested. Work stops here pending review.

### Successful localhost synthetic demonstration

On 2026-11-19 (Asia/Dubai), the user reported that the Phase 02B live
synthetic-data API demonstration on localhost completed successfully. This is
user-reported demonstration evidence; no additional route list, response codes
or launch command was supplied, and none is inferred here. It demonstrates the
local synthetic API path. SQL-provider validation remains mocked, with separately
verified native-driver import/signature compatibility. Actual SQL Server 2019
connection/query, schema, permissions, TLS and operational-data testing have not
been performed or accepted.

### Phase 02B GitHub review preparation

Review date: 2026-11-19 (Asia/Dubai). User authorized staging reviewed files only.
Branch is feature/phase02b-sql-provider; HEAD is
d9d8ffab7705950b80f6d00ca322527454714778. No commit/push/merge, remote query,
package installation or actual SQL connection is part of this review task.

All seven modified and four new files were reviewed: README.md; api/main.py;
api/config.py; api/providers.py; config/sql-provider.example.json; requirements.txt;
tests/test_providers.py; tests/test_engineering_harness.ps1; docs/PROJECT_STATE.md;
docs/TASKS.md; docs/RELEASE_GATES.md. Review found a literal allowlisted SELECT with
bound TOP value, bounded batches/overflow rejection, finite connection/query/lock
timeouts, cursor and connection cleanup on success/failure, validated explicit
configuration, masked credentials and safe errors with no synthetic fallback.
No application or test implementation was changed during review preparation.

Protected readiness implementation/tests, fixture, FIS-001, legacy loader and
historical Phase 01 evidence match a57936a. Original Phase 02A API tests and suite
selection match HEAD. The 22 original dependency pins remain unchanged; only
pymssql==2.3.3 was added, and all 23 pins match installed versions. pip check
exited 0 without installing or upgrading anything.

Fresh review checks, run from C:\AI\Projects\FIS4:

| Exact command | Actual result |
|---|---|
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | Exit 0; 79 tests; 0 failures/errors/skips |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable` | Exit 0; 74 tests; 0 failures/errors/skips; five external legacy tests excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | Exit 0; 12/12 harness checks passed, preserving all original scenarios |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1 -RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\phase02b-staging-review` | Exit 0; 26 proposed files; 0 violations; 6 manual leads, all dispositioned below |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | Exit 0 after actual staging; 26 index/working-tree files; 0 violations; 6 manual leads, all resolved below; REVIEW REQUIRED is the scanner's expected heuristic status |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --cached --check` | Exit 0; staged whitespace check passed |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code` | Exit 0; working files match staged contents after final documentation staging |

Test output was displayed using Select-Object -Last 14 with native exit status
preserved. Full mode includes all original 44 tests plus 35 provider tests;
Portable includes original 39 plus 35. SQL tests use injected fictional mocks.
The proposed scan copied the 22 tracked files plus the four explicitly reviewed
new files into a disposable workspace index; its exact cleanup path was checked
before removal. No real repository files were staged by that isolated scan.

Current scan disposition (each location appears in index and working copy):

| Location / rule | Disposition |
|---|---|
| api/config.py:29, credential-assignment | SecretStr password field declaration; no credential value present |
| api/providers.py:86, database-endpoint-assignment | Connector argument bound to validated runtime server configuration; no embedded endpoint |
| api/providers.py:89, credential-assignment | Connector argument receives the injected SecretStr value at runtime; no embedded credential or logging |

These six source-expression leads are resolved by source review. There are no
confirmed violations or unresolved manual findings; scanner rules are unchanged.
Security was rerun on the real index/working tree after authorized staging and
returned the same six dispositioned source-expression leads. Only the 11 reviewed
files listed above are staged; no environment, generated artifacts or additional
files are included. Test execution used these same application/test sources;
only review documentation changed afterward. Final documentation is restaged
and security rerun before stopping at the review gate. No commit, push or merge
has been performed; HEAD remains unchanged.
Read-only intent remains a connection hint; actual SQL permissions, schema/history,
TLS, consistency, timeout and load acceptance stay outside this review gate.

Proposed commit remains: `FIS4 Phase 02B: SQL provider architecture and mocked integration`.

### Implementation and scope

- New: `api/config.py`, `api/providers.py`,
  `config/sql-provider.example.json`, `tests/test_providers.py`.
- Updated: `api/main.py`, `requirements.txt`, `tests/test_engineering_harness.ps1`,
  README, PROJECT_STATE, TASKS and RELEASE_GATES.
- DataProvider exposes source and load_events. Synthetic remains the default,
  using the fixed fictional CSV; SQL is explicitly configured, lazy and injectable.
  Configuration performs no environment, credential-store or local-file discovery.
- SQL uses a literal allowlisted SELECT, a bound TOP limit, bounded fetchmany,
  strict event validation, row/span/snapshot-size limits and complete cleanup.
  Overflow fails rather than returning partial metrics. No fallback or retry.
  Read-only intent, required encryption, TDS 7.4 and finite login/query timeouts
  are passed to the connector. SQL work is serialized because FreeTDS timeouts
  are process-wide. These settings are mock-verified, not live-server claims.
- Credentials are separately injected SecretStr values, absent from config/Git.
  Test values are generated fictional strings. Driver exceptions are replaced
  with generic errors outside their exception context; no raw exception logging.
- Original readiness.py, 28 readiness tests, 16 Phase 02A API tests, fixture,
  legacy loader, suite selection, FIS-001 and historical Phase 01 report remain
  unchanged. Both providers reuse original normalization/snapshot/metric logic.
- Routes remain unchanged. Source supports synthetic/sql; responses gain
  X-FIS4-Data-Source. SQL failures return 503 with generic detail and source: sql;
  SQL empty/missing selections return 404. Synthetic bodies remain compatible.
- No live database/query, intranet, credentials, operational data, legacy edits,
  React, ML or offline packaging were used. Public driver docs/PyPI were consulted.

### Dependency boundary

Only addition: `pymssql==2.3.3`; all existing 22 exact pins unchanged. Official
release files include a CPython 3.13 Windows x64 wheel. Current dedicated FIS4
environment is Python 3.13.7 x64; driver metadata inspection found pymssql absent.
The user explicitly approved installing only pymssql==2.3.3 into the FIS4 .venv.
The approved binary/no-dependencies installation succeeded; native import reports
2.3.3 and FreeTDS v1.4.26. All 23 pins match installed metadata and pip check passes.
The real native connect signature (captured before mocking) accepts every adapter
keyword; connect was not called. Mock validation still works without the driver.
SQL Server 2019 transport, TLS identity and actual DB-API query behavior remain
unverified and must not be inferred from passing mocks. See README's official sources.

### Source contract and unresolved integration questions

Required contract target: [fis].[readiness_events_v1], exposing event_time,
textual tail, status and historical command. This view's existence is not claimed.
mod.VW_MNT_AIRCRAFT_SERVICEABILITY has NOT been inspected or assumed to be event
history and is not allowlisted. Object/column mappings, stable identity, timestamp
timezone, status mapping, command transfer history, retention/deletions and complete
initial/carry-in state remain unresolved. Optional platform/location/reason/hour
fields are unmapped. A current-only view cannot establish historical readiness.
Source owners must verify these semantics before actual integration acceptance.

### Executed verification (mocked SQL only)

Commands ran from C:\AI\Projects\FIS4. Each completed check below exited **0**.
Sandbox startup failed; local verification used the normal scoped approval path.

| Actual command | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_api.py -v` | Original 16/16 API contracts passed, unchanged |
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_providers.py -v` | Initial 34/34 passed; expanded 35/35 passed after log/source checks |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **79 passed** = original 44 + 35 new; 0 failures/errors/skips |
| Same verify command with `-TestMode Portable` | **74 passed** = original 39 + 35; five external legacy-reference tests excluded; 0 failures/errors/skips |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 passed**, preserving all original scenarios and portable selection |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 22 tracked index/working-tree files; 0 violations and 0 manual findings |
| Same security command with `-RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\phase02b-proposed-review` | 26 reviewed proposed files; 0 violations, 6 manual leads; all dispositioned below |
| `.\.venv\Scripts\python.exe -m pip install --no-deps --only-binary=:all: pymssql==2.3.3` | Explicitly approved installation; 2.3.3 CPython 3.13 Windows x64 wheel; no other packages changed |
| `.\.venv\Scripts\python.exe -B -c "import pymssql; from importlib.metadata import version; assert version('pymssql') == '2.3.3'; print('pymssql import/version: ' + pymssql.__version__); print(pymssql.get_dbversion())"` | Native import/version 2.3.3; FreeTDS v1.4.26; no connection |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements |
| Inline `.\.venv\Scripts\python.exe -B -`: compare all requirement pins with installed metadata | All 23 exact versions match |
| Inline `.\.venv\Scripts\python.exe -B -`: capture actual native connect signature before patching, bind mocked adapter kwargs, assert native function unused | Signature compatible; no native connect call |
| Inline `.\.venv\Scripts\python.exe -B -`: run full/portable suites with native connect blocked; block both imported legacy loader bindings for Portable | 79 full / 74 portable passed; zero native calls; zero portable external-loader calls |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | No whitespace errors |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code a57936a -- readiness.py tests/test_readiness.py tests/legacy_reference.py data/synthetic_readiness.csv docs/DECISIONS.md TEST_REPORT.md run_phase01.py docs/PUBLICATION_REVIEW.md` | Protected baseline unchanged |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code HEAD -- tests/test_api.py tests/suite_selection.py` | API baseline tests and selection unchanged |

Check output for full/portable/harness was displayed with Select-Object -Last 14;
native exit status was preserved. Existing pandas parsing and Starlette HTTPX
adapter warnings remain visible and do not change approved business semantics.
Full parity reads only existing hash-pinned legacy calculation sources; no files
or environments in the legacy project are modified.

### Security disposition and acceptance boundary

The four new source/template/test files were explicitly reviewed before being
copied with the 22 tracked files into a disposable workspace Git index. Only that
isolated copy was staged; the real index is untouched. The fixture was removed
after validating its exact resolved cleanup path.

Six scanner leads represent three source-code lines seen in index and working copy:
api/config.py line 29 is the SecretStr password field declaration (no value);
api/providers.py line 86 is the server keyword receiving validated configuration;
line 89 is the password keyword receiving an injected SecretStr at connection
time. These are reviewed code expressions, not embedded credentials or endpoints.
Disposition: expected adapter declarations/argument bindings; **no unresolved
manual security findings**. Scanner rules were not weakened. Final full verification,
tracked/proposed security checks are repeated after documentation updates; post-approved-staging scanning remains
mandatory before any later publication.

Mocked provider acceptance and real SQL integration acceptance are separate.
Native installation/import is verified after explicit approval. Open items:
all source mappings and history completeness; SELECT-only principal provisioning; TLS/certificate trust;
server-side isolation/consistency, timeouts, cancellation and load behavior.
Read-only intent is not permission enforcement, and query timeouts are not an
end-to-end deadline. No live acceptance was attempted or is authorized here.

Proposed commit: `FIS4 Phase 02B: SQL provider architecture and mocked integration`.

## Historical Phase 02A records

## Current Phase 02A acceptance record — 2026-11-18 (Asia/Dubai)

Synthetic FastAPI implemented; stopped at the Phase 02A gate. At implementation
handoff no staging, commit or push was performed. The subsequent authorized
staged review is recorded at the end of this document. The sections below preserve
historical Phase 01/01.6 evidence and constraints as they stood in those tasks.

### Publication correction

Phase 01.6 is committed as `bb3abfd036c2c7c88a03abf7e9cee628dd638f1c`, subject
`FIS4 Phase 01.6: engineering harness v1`. Local HEAD, main and cached origin/main
all resolve to that SHA. Working branch: `feature/phase02-fastapi`. Verified
using `git -c safe.directory=C:/AI/Projects/FIS4` with `show --stat --oneline
bb3abfd`, `log -3 --oneline`, `branch -avv`, and `rev-parse HEAD main origin/main`;
each exited 0. This supersedes stale awaiting-publication statements below.
No fetch or live remote verification occurred.

### Implementation and exact environment

- New: `api/__init__.py`, `api/main.py`, `requirements.txt`,
  `tests/test_api.py`, `tests/suite_selection.py`.
- Modified: README, verify script, harness regression script and the three
  state/tasks/gates documents. `readiness.py`, original 28 tests, reference
  loader, fixture, FIS-001, Phase 01 report/runner and historical publication
  review are unchanged.
- Dedicated ignored FIS4 `.venv`: CPython **3.13.7 x64**, pip **25.2**. Main pins:
  FastAPI **0.164.0**, Starlette **1.10.0**, Pydantic **2.14.3**, Uvicorn
  **0.54.0**, HTTPX **0.28.1**, pandas **2.3.3**, NumPy **2.3.4**. All 22 resolved
  runtime/test dependencies are pinned in requirements.txt; README explains uses.
- Health, fleet, command and distribution GET endpoints use only the fixed
  fictional fixture, with response schemas, query validation, 404/422 handling
  and generic 500 errors. README specifies the contract. No SQL, ML, React,
  credentials, operational data or offline packaging were used or implemented.
- Full verification retains 28 readiness tests plus 16 API tests. Portable mode
  runs 23 readiness plus 16 API tests, explicitly excluding five external tests.
  Original 11 harness scenarios retained, with one portable check added.

### Executed Phase 02A verification

Commands ran from `C:\AI\Projects\FIS4`; all completed commands below exited
**0**. Sandbox process setup failed; authorized execution ran outside it.

| Actual command/check | Actual result |
|---|---|
| `C:\Python313\python.exe -m venv .venv` | Dedicated environment created |
| `.\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx pandas==2.3.3 numpy==2.3.4` | Initial resolution succeeded |
| `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_api.py -v` | 16 API tests passed |
| `.\.venv\Scripts\python.exe -m pip freeze` | 22 versions recorded in requirements.txt |
| `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` | Exact pins satisfied |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **44 passed**, original 28 readiness + 16 API; 0 failures/errors/skips |
| Same command with `-TestMode Portable` | **39 passed**; five external tests excluded; 0 failures/errors/skips |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | **12/12 checks passed**, including original 11; explicit/automatic and portable suites pass |
| Inline stdin via `.\.venv\Scripts\python.exe -B -`: launch Uvicorn on ephemeral localhost port, GET health/three aggregates/OpenAPI, terminate in finally | **5/5 HTTP routes passed**; first-day serviceability 75%; server stopped |
| Inline stdin via `.\.venv\Scripts\python.exe -B -`: patch external loader to raise, select Portable, run unittest | **39 passed** with legacy loader blocked |

Final security/source-review evidence is recorded at the end of this document.

### Reviewed limitations

Inherited pandas date inference is retained to preserve baseline semantics.
Starlette deprecates its HTTPX test adapter; all contracts pass with the pins.
Warnings are not suppressed; adapter migration is deferred. Full parity still
requires external hash-pinned references; missing/changed files fail full mode.
Other platforms, production and offline compatibility are unverified. This is
local fictional-data use with no authentication; browser docs use CDN assets.
Publication requires separate approval and security review after approved staging.

## Historical Phase 01 / Phase 01.6 record

## Baseline

Phase 01 readiness baseline: **PASS**, 28 tests, zero failures/errors/skips.
Published GitHub baseline: [`a57936a8fff7e0502bceef008ea609fe4aef7379`](https://github.com/arbindchristy/FIS4/commit/a57936a8fff7e0502bceef008ea609fe4aef7379)
on `main` in the private `arbindchristy/FIS4` repository. The earlier publication
verified that local HEAD, origin/main, and the GitHub commit matched. This phase
does not contact GitHub or re-verify current remote state.

`TEST_REPORT.md` is the preserved Phase 01 execution evidence.
`PUBLICATION_REVIEW.md` is the historical pre-publication review, not a claim
that the already-published baseline remains unpublished.

## Business rule authority

Customer-approved formulas are FINAL under [FIS-001](DECISIONS.md):

```text
Serviceability = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
Availability   = (FMC + PMCM + PMCS) / Total * 100
```

NMCM remains in the serviceability denominator. Existing zero-denominator guards
remain unchanged. `readiness.py`, existing readiness tests, and the synthetic
readiness fixture are protected baseline artifacts in Phase 01.6.

## Phase 01.6 scope

Engineering harness v1 supplies local unittest verification and tracked-file
security checks. Project instructions and README describe the workflow; this
document records state, `TASKS.md` records work, `RELEASE_GATES.md` records gates,
and `DECISIONS.md` remains the single decision register.

No dependency installation, SQL, operational data, ML model loads, FastAPI,
React, or packaging work is authorized in this phase. No automatic commit or
push is authorized. The harness reuses the laptop's existing Python environment.

## Execution evidence

Initial Windows PowerShell 5.1 verification command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe
```

Actual result: exit 0; **28 tests passed**, zero failures/errors/skips.
The inherited pandas date-inference warning remains unchanged. The first
security-script attempt exposed a PowerShell 5.1 parameter-default issue; it
was corrected before acceptance.

Final acceptance results (Windows PowerShell **5.1.26100.9818**):

| Actual command/check | Actual result |
|---|---|
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe` | Exit 0; **11/11 harness checks passed**; explicit and automatic discovery each ran the unchanged 28 readiness tests successfully |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\security_check.ps1` | Exit 0; 11 tracked files; 0 confirmed violations; 0 manual-review findings |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\AI\Projects\FIS4\scripts\security_check.ps1 -RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\proposed-security-review` | Exit 0; all **17 proposed files** scanned in an isolated index; 0 confirmed violations; 0 manual-review findings; fixture then removed |
| Protected-file comparison against baseline commit | Module, both existing Python test files, synthetic fixture, original report, runner, and decision register byte-identical |
| Legacy metadata before/after final harness regression | **18,034 files unchanged**; source hashes additionally checked by existing parity tests |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --check` | Exit 0; no whitespace errors |
| Root index/HEAD | No staged changes; HEAD remains `a57936a8fff7e0502bceef008ea609fe4aef7379` |

The proposed-file scan used an explicit 17-file allowlist copied only from FIS4
into a disposable Git fixture. No legacy source was copied. No real working
repository files were staged; its tracked security scan intentionally does not
include the six new untracked files until approved staging.

Harness checks: explicit interpreter, automatic interpreter, invalid explicit
path (exit 2, no fallback), synthetic failing unittest (exit 1), zero tests
(exit 1), clean security fixture (exit 0), index review lead without value
disclosure (exit 0/REVIEW REQUIRED), working-tree review lead without value
disclosure, prohibited `.env` (exit 1), empty prohibited model-extension fixture
(exit 1, never loaded), and incomplete scan (exit 2). All passed. Synthetic
test repositories were removed after use. The earlier 10-check run also passed;
the final 11-check run added the explicit sensitive-file-type regression.

Phase 01.6 result at its task handoff: **PASS**. Publication subsequently
occurred as `bb3abfd`; see the locally verified correction above.
No network/SQL/package-install operations were used in that Phase 01.6 task.

## Git diff summary

Three existing files modified: `.gitignore` (ignore disposable harness fixtures),
`AGENTS.md` (end-of-task checks), and `README.md` (usage and limitations).
Their tracked diff is 71 inserted lines and no removals. Six new files are the
two scripts, `tests/test_engineering_harness.ps1`, and the three requested
state/backlog/gates documents. Untracked files are not included in `git diff
--stat` until staging. There are no readiness implementation/test/fixture changes.

## Known constraints

- The existing parity suite requires external, hash-pinned legacy source files
  at the documented laptop path. Those legacy files are not part of FIS4.
- Default system Python lacks pandas/NumPy; a compatible interpreter must be
  selected. No installation fallback is attempted.
- Security findings are heuristic, and manual findings require disposition.
  Untracked files need separate review and a post-staging scan before release.
- Sandbox command execution on this laptop has failed during process setup;
  verification uses authorized execution outside that failed sandbox. Git trust
  is scoped per command to the selected repository, not configured globally.
- Current verification is on this laptop, not an air-gapped destination. The
  Phase 00 destination/dependency/packaging uncertainties remain unresolved.

## Phase 02A final security and source review

- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
  .\scripts\security_check.ps1`: **exit 0**, 17 tracked files, zero confirmed
  violations, zero manual-review findings.
- Explicit source review of the five new files listed above: fixed synthetic
  source, aggregate-only API, fictional test inputs, dependency pins and suite
  classification only. No credentials, operational data, SQL/model access or
  additional source paths found. No unreviewed new files were added to the
  proposed content inventory.
- Proposed-content command: same security invocation with
  `-RepositoryPath C:\AI\Projects\FIS4\.harness-test-tmp\phase02a-proposed-review`:
  **exit 0**, **22 files**, zero violations and zero manual-review findings.
  Fixture inventory was the 17 tracked files plus the explicit five-new-file
  allowlist. Copies were staged only in its disposable index after source review;
  the working repository index was untouched. Fixture was removed after checking
  its resolved path matched the exact intended workspace directory.
- `git -c safe.directory=C:/AI/Projects/FIS4 diff --check`: **exit 0**.
  Source diff reviewed; protected baseline artifacts remain unchanged. No
  unresolved manual security findings. Expected LF/CRLF notices during isolated
  Git staging are line-ending notices, not content/security findings.
- Final full verification and tracked/proposed security checks are rerun after
  this evidence update. Publication remains pending; repeat the security check
  after separately approved staging in the working repository.

## Phase 02A staged GitHub review — 2026-11-18 (Asia/Dubai)

User authorized staging and local verification only. Branch verified as
`feature/phase02-fastapi`; HEAD remains
`bb3abfd036c2c7c88a03abf7e9cee628dd638f1c`. No commit, push, fetch, remote API
operation, dependency installation/upgrade or operational-system access occurred.
The sandbox process failed during setup; scoped local commands used the normal
approval mechanism. No machine-wide permissions or security settings changed.

All six modified and five new files were reviewed before explicit staging:
README.md; api/__init__.py; api/main.py; requirements.txt;
scripts/verify.ps1; tests/test_api.py; tests/suite_selection.py;
tests/test_engineering_harness.ps1; docs/PROJECT_STATE.md; docs/TASKS.md;
docs/RELEASE_GATES.md. Only these 11 files are staged; the environment and
generated artifacts remain excluded. Tests executed against working files
matching the staged index; only review documentation was updated afterward.

Protected staged files match both bb3abfd and the original Phase 01 baseline
a57936a: readiness.py, tests/test_readiness.py, tests/legacy_reference.py,
data/synthetic_readiness.csv, docs/DECISIONS.md, TEST_REPORT.md, run_phase01.py,
docs/PUBLICATION_REVIEW.md. FIS-001 formulas and zero-denominator guards remain
unchanged, including NMCM in the serviceability denominator.

Dependency review used installed importlib.metadata and pip's bundled requirement
parser, without network access. All 22 entries are exact equality pins matching
installed versions, and their active dependency closure matches the roots
FastAPI, Uvicorn, HTTPX, pandas and NumPy. No unrelated packages found. HTTPX is
for tests; OpenTelemetry API is required by FastAPI, with no exporter configured.
Requirements and installed dependencies were not changed during this review.

API source review confirms GET /health (liveness, no data read),
/api/v1/readiness/fleet, /api/v1/readiness/commands and
/api/v1/status-distribution. Aggregates read only the fixed fictional fixture.
No embedded credentials, operational data, SQL/model access, arbitrary data
paths or outbound service calls found. OpenAPI is local; browser documentation
intentionally uses CDN assets. No browser docs were opened during this review.

Commands below ran from C:\AI\Projects\FIS4. Each exited **0**; full and portable
tests had zero failures/errors/skips. Check output was displayed with
`| Select-Object -Last 14`, followed by `exit $LASTEXITCODE` to preserve status.

| Exact check command | Result |
|---|---|
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | 44/44 passed: 28 unchanged readiness + 16 API |
| `powershell.exe -NoProfile -File .\scripts\verify.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe -TestMode Portable` | 39/39 passed; five external-reference tests explicitly excluded |
| `powershell.exe -NoProfile -File .\tests\test_engineering_harness.ps1 -PythonExecutable C:\AI\Projects\FIS4\.venv\Scripts\python.exe` | 12/12 checks passed, including original 11 scenarios |
| `powershell.exe -NoProfile -File .\scripts\security_check.ps1` | 22 tracked index/working-tree files; zero violations and zero manual findings; repeated after review documentation staging |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements |
| `.\.venv\Scripts\python.exe -m pip list --format=json` | Installed versions match all 22 pins; pip 25.2 remains bootstrap-only |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --cached --exit-code a57936a -- readiness.py tests/test_readiness.py tests/legacy_reference.py data/synthetic_readiness.csv docs/DECISIONS.md TEST_REPORT.md run_phase01.py docs/PUBLICATION_REVIEW.md` | Protected baseline unchanged |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --exit-code` | No unstaged tracked differences |
| `git -c safe.directory=C:/AI/Projects/FIS4 diff --cached --check` | No staged whitespace errors |

Known limitations remain: inherited pandas date-inference warning, Starlette's
HTTPX test-adapter deprecation, external hash-pinned legacy sources required for
five full-suite tests, no authentication, CDN browser-doc assets, and unverified
production/offline/platform compatibility. No unresolved manual security findings.
Security review is heuristic and does not cover all Git history. No dependency
vulnerability database was queried because external network use was not authorized.

Proposed commit: `FIS4 Phase 02A: synthetic-data FastAPI backend`.
Staged review is complete; await explicit human approval before commit or push.
