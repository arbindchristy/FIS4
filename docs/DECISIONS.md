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
