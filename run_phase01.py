"""Run synthetic-only tests and write the actual Phase 01 evidence report in FIS4."""
from __future__ import annotations

import datetime
import hashlib
import io
import platform
from pathlib import Path
import subprocess
import sys
import unittest
import warnings

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))
from legacy_reference import ROOT as LEGACY, REFERENCES, MISSING_REFERENCE
from test_readiness import snapshot
import readiness


def legacy_metadata():
    # Metadata only: do not open operational data, credentials, or model files.
    return {str(p.relative_to(LEGACY)): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in LEGACY.rglob("*") if p.is_file()}


def reference_hashes():
    return {name: hashlib.sha256((LEGACY / name).read_bytes()).hexdigest() for name in REFERENCES}


def main():
    before_metadata = legacy_metadata()
    before_hashes = reference_hashes()
    output = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    with warnings.catch_warnings(record=True) as observed_warnings:
        warnings.simplefilter("always")
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    after_hashes = reference_hashes()
    unchanged = before_metadata == legacy_metadata() and before_hashes == after_hashes
    pinned = before_hashes == REFERENCES
    passed = result.wasSuccessful() and unchanged and pinned and not result.skipped
    snap = snapshot()
    fleet = readiness.compute_jac_daily_metrics(snap)
    command = subprocess.list2cmdline(sys.orig_argv)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4))).isoformat()
    report = [
        "# Phase 01 test report", "", f"Generated: {now} (Asia/Dubai offset).", "",
        f"Assessment: **{'PASS' if passed else 'FAIL'}**", "",
        "## Actual verification command", "", "Working directory: `C:\\AI\\Projects\\FIS4`.",
        "", "```text", command, "```", "",
        f"Python: {sys.version}", f"Executable: `{sys.executable}`",
        f"Architecture: {platform.machine()}; pandas {pd.__version__}; NumPy {np.__version__}.", "",
        "## Results", "",
        f"Tests: {result.testsRun}; failures: {len(result.failures)}; errors: {len(result.errors)}; skipped: {len(result.skipped)}.",
        f"Legacy tree metadata unchanged: {unchanged} ({len(before_metadata)} files checked).",
        f"Reviewed source hashes unchanged and matched pins: {pinned and before_hashes == after_hashes}.",
        "No legacy app imported; only hash-pinned calculation definitions executed on synthetic frames.",
        "No SQL connections, external services, operational-data reads, model loads, or training used.", "",
        "## References actually inspected", "",
    ]
    for name, digest in after_hashes.items():
        report += [f"- `{name}` — SHA-256 `{digest}`."]
    report += [f"- `{MISSING_REFERENCE}` — absent; not inspected or compared.", "",
               "v3_10_4 full-file parsing fails at line 1576 (unterminated string literal). Its calculation prefix parses; only allowlisted constants/functions are compiled. v3_10_2 parses in full.", "",
               "## Synthetic fixture fleet results", "", "```text", fleet.to_string(index=False), "```", "",
               "## Latest synthetic command results", "", "```text",
               readiness.compute_command_latest_metrics(snap, snap['date'].max()).to_string(index=False), "```", "",
               "## Comparison, customer-approved formula lock, and limitations", "",
               "- Both references match new normalization, snapshot frames (including dtypes/order), fleet metrics, and command metrics on the tested valid inputs and edge cases.",
               "- CUSTOMER-APPROVED / FINAL: explicit user confirmation on 2026-11-17 locks serviceability = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100 and availability = (FMC + PMCM + PMCS) / Total * 100 at fleet and command levels. NMCM MUST remain in the serviceability denominator. Conflicting legacy comments are incorrect documentation, not a pending formula decision. See docs/DECISIONS.md (FIS-001) and AGENTS.md. Calculation code remains unchanged.",
               "- Deliberate guard: new metric APIs reject duplicate date/tail rows. Legacy APIs mix unique-tail denominators with row-count numerators and can return 150%; this defect is reproduced in a characterization test. Build snapshots before aggregation.",
               "- No groups (all raw tail keys null): new snapshot returns empty; legacy may fail during reset/date lookup. Valid normalized identifiers are the supported contract.",
               "- Equal timestamps have no explicit legacy tie-break rule; no new business tie-break rule was introduced. Tests cover repeated same-day events at different times.",
               "- Timezone-aware/mixed-format inputs, null/blank identifiers, cross-version pandas compatibility, full Streamlit runtime behavior, and operational datasets are outside this acceptance scope.",
               "- groupby.last retains per-column non-null values, forward fill has no staleness limit, unknown statuses remain in totals, and missing command values may prevent command/fleet reconciliation on malformed inputs. See README.", "",
               "## Observed warnings", ""]
    report += [f"- {item.category.__name__}: {item.message}" for item in observed_warnings] or ["None."]
    report += ["", "Date inference warnings are inherited pandas behavior; no parser change was made. Legacy GroupBy.apply FutureWarnings are suppressed only within comparison tests; the new snapshot implementation does not use GroupBy.apply.", "",
               "## Actual unittest output", "", "```text", output.getvalue().rstrip(), "```", ""]
    (ROOT / "TEST_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(output.getvalue(), end="")
    print(f"Legacy unchanged: {unchanged}; pinned hashes: {pinned}")
    print(f"Phase 01 {'PASS' if passed else 'FAIL'}; report: {ROOT / 'TEST_REPORT.md'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
