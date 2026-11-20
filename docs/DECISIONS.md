# FIS v4 decisions

## FIS-001: Readiness formulas — CUSTOMER-APPROVED / FINAL

Date: 2026-11-17 (Asia/Dubai).

Authority: explicit user confirmation, relaying customer approval in the
"FIS v4 — Customer-Approved Formula Lock" instruction. This approval is based
on the original Streamlit v3.10.4 **executable** calculations, not its conflicting
comments. No separate customer communication or artifact was accessed.

The user explicitly instructed: "NMCM MUST remain in the serviceability
denominator. It must NOT be excluded."

### Locked formulas

```text
SERVICEABILITY (%) = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100
AVAILABILITY (%)   = (FMC + PMCM + PMCS) / Total * 100
```

These formulas apply identically at fleet and command levels. `Total` is the
distinct aircraft-tail count in a valid daily snapshot. PMC represents PMCM
plus PMCS. NMCM remains in Total and in the serviceability denominator.
The existing behavior returning 0% when the applicable denominator is not
positive is retained unchanged.

### Resolution of legacy documentation conflict

Legacy metric docstrings and one comment incorrectly describe subtracting
NMCM as well as NMCS and DEPOT. Those statements are historical documentation
errors, not alternative business rules. Customer approval resolves the
Phase 01 formula question in favor of the executable behavior.

Legacy files remain read-only and are not corrected in place. FIS4 documentation
must state the locked formulas and may describe the old discrepancy only when
explicitly labeling NMCM exclusion as incorrect.

### Change control

Do not alter the formulas or adjust regression expectations to accept NMCM
exclusion. A change requires a new explicit customer-authorized instruction
superseding this decision and a recorded decision update. Routine refactoring,
future API/UI development, or conflicting legacy comments do not authorize a
business formula change. The durable project instruction is in `../AGENTS.md`.

### Verification

`readiness.py` already implements the approved formulas in `_metrics`.
Both `compute_jac_daily_metrics` and `compute_command_latest_metrics` call
that helper. No calculation implementation changes are required or authorized.

The synthetic regression with six tails, three ready, one NMCS, one NMCM,
and one DEPOT must remain **75% serviceability and 50% availability**.
For the latest synthetic command B, two ready tails out of four, including
one NMCM and one DEPOT, must remain **66.666667% serviceability and 50%
availability** (display precision only).

See `../TEST_REPORT.md` for the actual rerun command, all 28 test results,
legacy-versus-new comparison, and legacy preservation evidence.

## FIS-002: Offline-First Deployment and Single Product Codebase — CUSTOMER REQUIREMENT / APPROVED

Date: 2026-11-20 (Asia/Dubai).

Authority: the user's explicit "FIS4 architecture decision — FIS-002" instruction,
relaying the customer requirement. No separate customer communication was accessed.

### Decision

FIS4 must be fully developed, integrated and acceptance-tested before
security-approved transfer to the air-gapped Windows intranet. Transfer is not
an opportunity to finish development, install missing dependencies, train models
or repair source code on the destination machine.

The cloud customer demonstration and intranet deployment are one product with
one codebase. They must share the same FastAPI business logic, readiness
calculations, rule-based prediction engine, ML inference code and API contracts.
Cloud hosting is a deployment configuration, not a separate implementation of
application logic. Data-source and hosting configuration may differ; application
rules and API semantics must remain shared.

### Required deployment behavior

1. Deliver one self-contained Windows x64 offline release ZIP.
2. Bundle compatible Python runtime, dependencies, native libraries, compiled
   React assets and verified ML artifacts in that release.
3. Require no Node.js, npm, pip, internet access or model training on the intranet.
4. Minimize configuration to the approved SQL connection, credentials supplied
   through an approved local secret mechanism, and required deployment settings.
   Do not embed deployment credentials in source code or release artifacts.
5. Preserve synthetic mode for pre-connection verification.
6. Supply deterministic start, stop, health-check, diagnostics and rollback scripts.
7. Never require manual source-code modification during deployment.
8. Build and test the exact release package on a clean, network-isolated Windows
   x64 environment before transfer.
9. Generate integrity manifests, a dependency inventory, verification evidence
   and a security-review package tied to that exact release.
10. Document SQL schema, permission, TLS and operational dependencies that cannot
    be eliminated by packaging. Packaging does not waive integration acceptance
    or make unresolved external dependencies disappear.
11. Treat cloud hosting as deployment configuration while preserving the shared
    application implementation and API contracts.
12. Preserve all FIS-001 customer-approved formulas and regression tests,
    including NMCM in the serviceability denominator and existing zero guards.

### Acceptance and change-control consequences

The release gates in RELEASE_GATES.md require evidence for product integration,
cloud/intranet code and contract parity, complete offline contents, destination
prerequisite independence, configuration-only deployment, operational scripts,
synthetic pre-connection checks, exact-package isolated validation, integrity and
security review, and documented SQL dependencies before transfer approval.

This decision records requirements, not a claim that prediction, ML, packaging,
SQL integration or release acceptance is already implemented or verified. Those
activities retain their existing separate authorization and acceptance boundaries.
This documentation-only instruction does not authorize package installation,
application changes, database/credential/model access, deployment, commit or push.
FIS-002 does not supersede or weaken FIS-001.
