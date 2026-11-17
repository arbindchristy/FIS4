# Phase 01 test report

Generated: 2026-11-17T20:26:50.578407+04:00 (Asia/Dubai offset).

Assessment: **PASS**

## Actual verification command

Working directory: `C:\AI\Projects\FIS4`.

```text
C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe -B run_phase01.py
```

Python: 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)]
Executable: `C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe`
Architecture: AMD64; pandas 2.3.3; NumPy 2.3.4.

## Results

Tests: 28; failures: 0; errors: 0; skipped: 0.
Legacy tree metadata unchanged: True (18034 files checked).
Reviewed source hashes unchanged and matched pins: True.
No legacy app imported; only hash-pinned calculation definitions executed on synthetic frames.
No SQL connections, external services, operational-data reads, model loads, or training used.

## References actually inspected

- `streamlit_sql_portal_v3_10_2.py` — SHA-256 `05bb1c077ec77d5b21bc7ce53fe0c8c8bb7188bbe8356099bc9fbe75e2b8dce7`.
- `streamlit_sql_portal_v3_10_4.py` — SHA-256 `6b1ef3451ec9a47203cf96d1cd7a83bb872ed64bd3bce523c9c744ca4be06980`.
- `streamlit_sql_portal_v3_10_5_corrected.py` — absent; not inspected or compared.

v3_10_4 full-file parsing fails at line 1576 (unterminated string literal). Its calculation prefix parses; only allowlisted constants/functions are compiled. v3_10_2 parses in full.

## Synthetic fixture fleet results

```text
      date  total_tails  fmc_tails  pmc_tails  nmcm_tails  nmcs_tails  depot_tails   svc_pct  avail_pct
2026-01-01            6          1          2           1           1            1 75.000000  50.000000
2026-01-02            6          1          2           1           1            1 75.000000  50.000000
2026-01-03            7          3          2           1           0            1 83.333333  71.428571
```

## Latest synthetic command results

```text
command  total_tails  fmc_tails  pmc_tails  nmcm_tails  nmcs_tails  depot_tails    svc_pct  avail_pct
      A            3          2          1           0           0            0 100.000000      100.0
      B            4          1          1           1           0            1  66.666667       50.0
```

## Comparison, customer-approved formula lock, and limitations

- Both references match new normalization, snapshot frames (including dtypes/order), fleet metrics, and command metrics on the tested valid inputs and edge cases.
- CUSTOMER-APPROVED / FINAL: explicit user confirmation on 2026-11-17 locks serviceability = (FMC + PMCM + PMCS) / (Total - DEPOT - NMCS) * 100 and availability = (FMC + PMCM + PMCS) / Total * 100 at fleet and command levels. NMCM MUST remain in the serviceability denominator. Conflicting legacy comments are incorrect documentation, not a pending formula decision. See docs/DECISIONS.md (FIS-001) and AGENTS.md. Calculation code remains unchanged.
- Deliberate guard: new metric APIs reject duplicate date/tail rows. Legacy APIs mix unique-tail denominators with row-count numerators and can return 150%; this defect is reproduced in a characterization test. Build snapshots before aggregation.
- No groups (all raw tail keys null): new snapshot returns empty; legacy may fail during reset/date lookup. Valid normalized identifiers are the supported contract.
- Equal timestamps have no explicit legacy tie-break rule; no new business tie-break rule was introduced. Tests cover repeated same-day events at different times.
- Timezone-aware/mixed-format inputs, null/blank identifiers, cross-version pandas compatibility, full Streamlit runtime behavior, and operational datasets are outside this acceptance scope.
- groupby.last retains per-column non-null values, forward fill has no staleness limit, unknown statuses remain in totals, and missing command values may prevent command/fleet reconciliation on malformed inputs. See README.

## Observed warnings

- UserWarning: Could not infer format, so each element will be parsed individually, falling back to `dateutil`. To ensure parsing is consistent and as-expected, please specify a format.

Date inference warnings are inherited pandas behavior; no parser change was made. Legacy GroupBy.apply FutureWarnings are suppressed only within comparison tests; the new snapshot implementation does not use GroupBy.apply.

## Actual unittest output

```text
test_constants_and_normalization_match_both_references (test_readiness.LegacyParityTests.test_constants_and_normalization_match_both_references) ... ok
test_edge_snapshots_and_formulas_match_both_references (test_readiness.LegacyParityTests.test_edge_snapshots_and_formulas_match_both_references) ... ok
test_full_fixture_snapshots_and_metrics_match_both_references (test_readiness.LegacyParityTests.test_full_fixture_snapshots_and_metrics_match_both_references) ... ok
test_legacy_raw_duplicate_counting_defect_is_explicit (test_readiness.LegacyParityTests.test_legacy_raw_duplicate_counting_defect_is_explicit) ... ok
test_command_known_answers_and_date_normalization (test_readiness.MetricTests.test_command_known_answers_and_date_normalization) ... ok
test_direct_duplicate_snapshot_rejected_in_both_metric_apis (test_readiness.MetricTests.test_direct_duplicate_snapshot_rejected_in_both_metric_apis) ... ok
test_duplicate_events_do_not_inflate_snapshot_metrics (test_readiness.MetricTests.test_duplicate_events_do_not_inflate_snapshot_metrics) ... ok
test_empty_missing_command_and_absent_requested_date (test_readiness.MetricTests.test_empty_missing_command_and_absent_requested_date) ... ok
test_fleet_command_count_and_denominator_weighted_consistency (test_readiness.MetricTests.test_fleet_command_count_and_denominator_weighted_consistency) ... ok
test_fleet_known_answers_and_nmcm_denominator (test_readiness.MetricTests.test_fleet_known_answers_and_nmcm_denominator) ... ok
test_nonempty_metrics_require_snapshot_columns (test_readiness.MetricTests.test_nonempty_metrics_require_snapshot_columns) ... ok
test_true_null_commands_do_not_reconcile_and_match_legacy (test_readiness.MetricTests.test_true_null_commands_do_not_reconcile_and_match_legacy) ... ok
test_unknown_status_stays_in_total_and_denominator (test_readiness.MetricTests.test_unknown_status_stays_in_total_and_denominator) ... ok
test_zero_effective_denominator (test_readiness.MetricTests.test_zero_effective_denominator) ... ok
test_aliases_dates_numeric_and_tail_text (test_readiness.NormalizationTests.test_aliases_dates_numeric_and_tail_text) ... ok
test_canonical_codes (test_readiness.NormalizationTests.test_canonical_codes) ... ok
test_every_legacy_alias (test_readiness.NormalizationTests.test_every_legacy_alias) ... ok
test_header_whitespace_remains_unmatched (test_readiness.NormalizationTests.test_header_whitespace_remains_unmatched) ... ok
test_unknown_and_null_statuses_are_not_reclassified (test_readiness.NormalizationTests.test_unknown_and_null_statuses_are_not_reclassified) ... ok
test_all_null_raw_tail_keys_return_empty (test_readiness.SnapshotTests.test_all_null_raw_tail_keys_return_empty) ... ok
test_command_transfer_is_forward_filled (test_readiness.SnapshotTests.test_command_transfer_is_forward_filled) ... ok
test_inputs_are_unchanged (test_readiness.SnapshotTests.test_inputs_are_unchanged) ... ok
test_invalid_dates_and_missing_columns (test_readiness.SnapshotTests.test_invalid_dates_and_missing_columns) ... ok
test_last_is_per_column_not_whole_event (test_readiness.SnapshotTests.test_last_is_per_column_not_whole_event) ... ok
test_last_same_day_status_wins_even_when_input_is_reversed (test_readiness.SnapshotTests.test_last_same_day_status_wins_even_when_input_is_reversed) ... ok
test_no_backfill_or_extension_to_today (test_readiness.SnapshotTests.test_no_backfill_or_extension_to_today) ... ok
test_normalized_null_text_is_not_forward_filled_as_null (test_readiness.SnapshotTests.test_normalized_null_text_is_not_forward_filled_as_null) ... ok
test_unique_daily_tail_rows_and_calendar_gap (test_readiness.SnapshotTests.test_unique_daily_tail_rows_and_calendar_gap) ... ok

----------------------------------------------------------------------
Ran 28 tests in 1.193s

OK
```
