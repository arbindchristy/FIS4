# FIS v4 project instructions

## Customer-approved readiness formula lock

The user explicitly confirmed the original Streamlit v3.10.4 executable
readiness formulas as FINAL. See [docs/DECISIONS.md](docs/DECISIONS.md), decision
FIS-001. Apply these rules to every fleet and command calculation:

```text
SERVICEABILITY (%) = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
AVAILABILITY (%)   = (FMC + PMCM + PMCS) / Total * 100
```

NMCM MUST remain in the serviceability denominator. Do not subtract NMCM.
Do not change these business formulas, status contributions, or regression
expectations without a new explicit customer-authorized instruction that
supersedes FIS-001. Legacy comments suggesting NMCM exclusion are incorrect
documentation and must not override the approved executable behavior.
Do not treat the documentation discrepancy as an unresolved formula decision.

Preserve the existing zero-denominator guards. Fleet and command metrics must
use the same formulas. Run the existing 28 Phase 01 tests after relevant work;
do not weaken tests to permit a formula change.

## Offline-first deployment and single product codebase

Follow the customer requirement [FIS-002](docs/DECISIONS.md): FIS4 must be fully
developed, integrated and acceptance-tested before security-approved transfer
to the air-gapped Windows intranet.

- Maintain one product codebase for cloud customer demonstration and intranet
  deployment: shared FastAPI business logic, readiness calculations, rule-based
  prediction engine, ML inference code and API contracts. Cloud hosting is
  deployment configuration, not a separate implementation of application logic.
- Deliver one self-contained Windows x64 offline release ZIP bundling compatible
  Python runtime, dependencies, native libraries, compiled React assets and
  verified ML artifacts. The intranet must require no Node.js, npm, pip, internet
  access or model training.
- Limit deployment configuration to the approved SQL connection, credentials
  through an approved local secret mechanism, and required deployment settings.
  Never require manual source-code edits during deployment or embed credentials
  in source or release artifacts.
- Preserve synthetic mode for pre-connection verification. Supply deterministic
  start, stop, health-check, diagnostics and rollback scripts.
- Build and test the exact release package in a clean, network-isolated Windows
  x64 environment before transfer. Generate integrity manifests, dependency
  inventory, verification evidence and a security-review package for that release.
- Document unavoidable SQL schema, permission, TLS and operational dependencies;
  packaging does not substitute for their acceptance evidence.
- Preserve FIS-001 formulas, zero-denominator guards and protected regression
  tests. FIS-002 authorizes no formula change and makes no claim that future
  product components or release capabilities already exist.

Apply the release gates before transfer. Implementation, package installation,
database/credential/model access, packaging, deployment, commit and push still
require authorization for the active task; a recorded requirement is not itself
permission to execute those activities.

## Streamlit architecture contract

Before changing history, readiness, platform, SQL integration or prediction code,
read [docs/STREAMLIT_PARITY.md](docs/STREAMLIT_PARITY.md) and
[docs/INTRANET_INTEGRATION_CONTRACT.md](docs/INTRANET_INTEGRATION_CONTRACT.md),
alongside FIS-001/FIS-002 and FIS-003 in docs/DECISIONS.md. Preserve the approved
history-view semantics, current-assignment hierarchy, internal-only battalion
mapping and independent platform dimension. Do not silently repair or reinterpret
legacy logic, substitute a source/trainer, invent transfers, change formulas or
assume model compatibility. Record unresolved evidence and obtain explicit approval
for semantic changes. Local sanitized syntax damage does not invalidate the
working intranet reference. These documents authorize no SQL/model execution,
training, dependency installation, application changes or deployment by themselves.

## Project boundaries

- Legacy reference `C:\AI\Projects\fleet_cpi_suite` is read-only.
- Keep new work inside `C:\AI\Projects\FIS4`.
- Do not access credentials, SQL, operational fleet data, or joblib models
  without a separate explicit instruction authorizing that scope.
- Do not install packages or begin FastAPI, React, or packaging work without
  a separate instruction.

## End-of-task engineering checks

Run `scripts/verify.ps1` and `scripts/security_check.ps1` at the end of future
tasks. Use `-PythonExecutable` when interpreter selection must be explicit.
Record the actual commands, exit codes, test count/results, and any unresolved
manual security findings in the task report. A nonzero check exit code blocks
completion; manual-review findings require disposition before publication.
The security check covers tracked index and working-tree content; untracked
files require explicit review before staging, followed by another security check.

Keep `docs/PROJECT_STATE.md`, `docs/TASKS.md`, and `docs/RELEASE_GATES.md` current.
Reuse `docs/DECISIONS.md` for decisions and `TEST_REPORT.md` for Phase 01 evidence;
do not create competing governance files or rewrite historical test evidence.
Do not commit or push without the approval required by the active task.
