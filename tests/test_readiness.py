from pathlib import Path
import unittest
import warnings

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import readiness as new
from legacy_reference import REFERENCES, load_reference

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "synthetic_readiness.csv"


def events():
    return pd.read_csv(FIXTURE, dtype={"tail": str})


def snapshot():
    return new.build_tail_daily_snapshot(new.coalesce_columns(events()))


class NormalizationTests(unittest.TestCase):
    def test_every_legacy_alias(self):
        values = pd.Series([f"  {alias.lower()}  " for alias in new.STATUS_CANON])
        self.assertEqual(new.normalize_status(values).tolist(), list(new.STATUS_CANON.values()))

    def test_canonical_codes(self):
        self.assertEqual(set(new.STATUS_CANON.values()), set(new.CANONICAL_STATUSES))
        self.assertEqual(new.normalize_status(pd.Series(new.CANONICAL_STATUSES)).tolist(),
                         list(new.CANONICAL_STATUSES))

    def test_unknown_and_null_statuses_are_not_reclassified(self):
        values = pd.Series([" mystery ", None, np.nan, ""])
        self.assertEqual(new.normalize_status(values).tolist(), ["MYSTERY", "NONE", "NAN", ""])

    def test_aliases_dates_numeric_and_tail_text(self):
        raw = pd.DataFrame({"CREATED_ON_": ["2026-01-01", "invalid"],
                            "TAIL_NUM_": [" 0001 ", "0002"], "COND_": ["mc", "nmc"],
                            "HOURS_TO_INSP": ["15.5", "bad"], "CODE_": [" A ", "B"]})
        actual = new.coalesce_columns(raw)
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual.iloc[0]["tail"], "0001")
        self.assertEqual(actual.iloc[0]["status"], "FMC")
        self.assertEqual(actual.iloc[0]["command"], "A")
        self.assertEqual(actual.iloc[0]["hrs_to_insp"], 15.5)

    def test_header_whitespace_remains_unmatched(self):
        actual = new.coalesce_columns(pd.DataFrame({"hrs_to_phase ": ["10"]}))
        self.assertIn("hrs_to_phase ", actual)
        self.assertNotIn("hrs_to_phase", actual)


class SnapshotTests(unittest.TestCase):
    def test_unique_daily_tail_rows_and_calendar_gap(self):
        actual = snapshot()
        self.assertEqual(len(actual), 19)
        self.assertFalse(actual.duplicated(["date", "tail"]).any())
        self.assertEqual(actual.groupby("date")["tail"].nunique().tolist(), [6, 6, 7])
        self.assertEqual(actual[actual["date"] == pd.Timestamp("2026-01-02")]["tail"].nunique(), 6)

    def test_last_same_day_status_wins_even_when_input_is_reversed(self):
        actual = new.build_tail_daily_snapshot(new.coalesce_columns(events().iloc[::-1]))
        tail = actual[actual["tail"] == "0001"]
        self.assertEqual(tail["status"].tolist(), ["FMC", "FMC", "FMC"])

    def test_no_backfill_or_extension_to_today(self):
        actual = snapshot()
        self.assertEqual(actual[actual["tail"] == "0007"]["date"].tolist(),
                         [pd.Timestamp("2026-01-03")])
        self.assertEqual(actual["date"].max(), pd.Timestamp("2026-01-03"))

    def test_command_transfer_is_forward_filled(self):
        tail = snapshot().query("tail == '0002'")
        self.assertEqual(tail["command"].tolist(), ["A", "A", "B"])

    def test_last_is_per_column_not_whole_event(self):
        raw = pd.DataFrame({"date": ["2026-01-01 08:00", "2026-01-01 16:00"],
                            "tail": ["T", "T"], "status": ["FMC", "NMCM"],
                            "command": ["A", None], "hrs_to_insp": [20.0, np.nan]})
        actual = new.build_tail_daily_snapshot(raw).iloc[0]
        self.assertEqual(actual["status"], "NMCM")
        self.assertEqual(actual["command"], "A")
        self.assertEqual(actual["hrs_to_insp"], 20.0)

    def test_normalized_null_text_is_not_forward_filled_as_null(self):
        raw = pd.DataFrame({"date": ["2026-01-01 08:00", "2026-01-01 16:00"],
                            "tail": ["T", "T"], "status": ["FMC", "NMCM"],
                            "command": ["A", None]})
        actual = new.build_tail_daily_snapshot(new.coalesce_columns(raw)).iloc[0]
        self.assertEqual(actual["command"], "None")

    def test_invalid_dates_and_missing_columns(self):
        self.assertNotIn("BAD", snapshot()["tail"].tolist())
        self.assertTrue(new.build_tail_daily_snapshot(pd.DataFrame({"tail": ["T"]})).empty)
        bad = pd.DataFrame({"date": ["bad"], "tail": ["T"], "status": ["FMC"]})
        self.assertTrue(new.build_tail_daily_snapshot(bad).empty)

    def test_inputs_are_unchanged(self):
        raw = events()
        before = raw.copy(deep=True)
        clean = new.coalesce_columns(raw)
        clean_before = clean.copy(deep=True)
        built = new.build_tail_daily_snapshot(clean)
        built_before = built.copy(deep=True)
        new.compute_jac_daily_metrics(built)
        new.compute_command_latest_metrics(built, "2026-01-03")
        assert_frame_equal(raw, before)
        assert_frame_equal(clean, clean_before)
        assert_frame_equal(built, built_before)

    def test_all_null_raw_tail_keys_return_empty(self):
        raw = pd.DataFrame({"date": ["2026-01-01"], "tail": [np.nan], "status": ["FMC"]})
        self.assertTrue(new.build_tail_daily_snapshot(raw).empty)


class MetricTests(unittest.TestCase):
    def test_fleet_known_answers_and_nmcm_denominator(self):
        actual = new.compute_jac_daily_metrics(snapshot())
        expected_counts = [[6, 1, 2, 1, 1, 1], [6, 1, 2, 1, 1, 1], [7, 3, 2, 1, 0, 1]]
        count_columns = ["total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails", "depot_tails"]
        self.assertEqual(actual[count_columns].values.tolist(), expected_counts)
        np.testing.assert_allclose(actual["svc_pct"], [75, 75, 500 / 6])
        np.testing.assert_allclose(actual["avail_pct"], [50, 50, 500 / 7])

    def test_command_known_answers_and_date_normalization(self):
        actual = new.compute_command_latest_metrics(snapshot(), "2026-01-03 23:59").set_index("command")
        self.assertEqual(actual.loc["A", "total_tails"], 3)
        self.assertEqual(actual.loc["B", "total_tails"], 4)
        self.assertAlmostEqual(actual.loc["A", "svc_pct"], 100)
        self.assertAlmostEqual(actual.loc["A", "avail_pct"], 100)
        self.assertAlmostEqual(actual.loc["B", "svc_pct"], 200 / 3)
        self.assertAlmostEqual(actual.loc["B", "avail_pct"], 50)

    def test_fleet_command_count_and_denominator_weighted_consistency(self):
        snap = snapshot()
        for _, fleet in new.compute_jac_daily_metrics(snap).iterrows():
            commands = new.compute_command_latest_metrics(snap, fleet["date"])
            for col in ["total_tails", "fmc_tails", "pmc_tails", "nmcm_tails", "nmcs_tails", "depot_tails"]:
                self.assertEqual(commands[col].sum(), fleet[col])
            denominators = commands["total_tails"] - commands["nmcs_tails"] - commands["depot_tails"]
            svc = (commands["svc_pct"] * denominators).sum() / denominators.sum()
            avail = (commands["avail_pct"] * commands["total_tails"]).sum() / commands["total_tails"].sum()
            self.assertAlmostEqual(svc, fleet["svc_pct"])
            self.assertAlmostEqual(avail, fleet["avail_pct"])

    def test_duplicate_events_do_not_inflate_snapshot_metrics(self):
        raw = pd.concat([events(), events()], ignore_index=True)
        assert_frame_equal(new.compute_jac_daily_metrics(new.build_tail_daily_snapshot(new.coalesce_columns(raw))),
                           new.compute_jac_daily_metrics(snapshot()))

    def test_direct_duplicate_snapshot_rejected_in_both_metric_apis(self):
        snap = snapshot()
        duplicated = pd.concat([snap, snap.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "one row per date/tail"):
            new.compute_jac_daily_metrics(duplicated)
        with self.assertRaisesRegex(ValueError, "one row per date/tail"):
            new.compute_command_latest_metrics(duplicated, "2026-01-03")

    def test_zero_effective_denominator(self):
        raw = pd.DataFrame({"date": ["2026-01-01"] * 2, "tail": ["T1", "T2"],
                            "status": ["NMCS", "DEPOT"], "command": ["A", "A"]})
        snap = new.build_tail_daily_snapshot(raw)
        for actual in [new.compute_jac_daily_metrics(snap), new.compute_command_latest_metrics(snap, "2026-01-01")]:
            self.assertEqual(actual.iloc[0]["svc_pct"], 0)
            self.assertEqual(actual.iloc[0]["avail_pct"], 0)

    def test_unknown_status_stays_in_total_and_denominator(self):
        raw = pd.DataFrame({"date": ["2026-01-01"] * 2, "tail": ["T1", "T2"],
                            "status": ["FMC", "mystery"]})
        row = new.compute_jac_daily_metrics(new.build_tail_daily_snapshot(raw)).iloc[0]
        self.assertEqual(row["total_tails"], 2)
        self.assertEqual(row["svc_pct"], 50)
        self.assertEqual(row["avail_pct"], 50)

    def test_empty_missing_command_and_absent_requested_date(self):
        self.assertTrue(new.compute_jac_daily_metrics(pd.DataFrame()).empty)
        self.assertTrue(new.compute_command_latest_metrics(pd.DataFrame(), "2026-01-01").empty)
        self.assertTrue(new.compute_command_latest_metrics(snapshot().drop(columns="command"), "2026-01-01").empty)
        self.assertTrue(new.compute_command_latest_metrics(snapshot(), "2030-01-01").empty)

    def test_nonempty_metrics_require_snapshot_columns(self):
        with self.assertRaisesRegex(ValueError, "date, tail, and status"):
            new.compute_jac_daily_metrics(pd.DataFrame({"tail": ["T"]}))

    def test_true_null_commands_do_not_reconcile_and_match_legacy(self):
        raw = pd.DataFrame({"date": ["2026-01-01"] * 2, "tail": ["T", "U"],
                            "status": ["FMC", "NMCM"], "command": ["A", None]})
        snap = new.build_tail_daily_snapshot(raw)
        fleet = new.compute_jac_daily_metrics(snap)
        commands = new.compute_command_latest_metrics(snap, "2026-01-01")
        self.assertEqual(fleet.iloc[0]["total_tails"], 2)
        self.assertEqual(commands["total_tails"].sum(), 1)
        for name in REFERENCES:
            reference = load_reference(name)
            assert_frame_equal(commands, reference["compute_command_latest_metrics"](snap, "2026-01-01"))


class LegacyParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = {name: load_reference(name) for name in REFERENCES}

    def test_constants_and_normalization_match_both_references(self):
        raw = events()
        extra = pd.DataFrame({"date": ["2026-01-01"] * 4, "tail": ["X", "Y", "Z", "W"],
                              "status": ["unknown", None, np.nan, ""]})
        for name, reference in self.legacy.items():
            with self.subTest(reference=name):
                self.assertEqual(new.STATUS_CANON, reference["STATUS_CANON"])
                self.assertEqual(new.CANDIDATE_COLS, reference["CANDIDATE_COLS"])
                for data in [raw, extra]:
                    assert_frame_equal(new.coalesce_columns(data), reference["coalesce_columns"](data))

    def test_full_fixture_snapshots_and_metrics_match_both_references(self):
        for name, reference in self.legacy.items():
            with self.subTest(reference=name), warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                clean = reference["coalesce_columns"](events())
                old = reference["build_tail_daily_snapshot"](clean)
                current = new.build_tail_daily_snapshot(clean)
                assert_frame_equal(current, old)  # Includes order, index, columns and dtypes.
                assert_frame_equal(new.compute_jac_daily_metrics(current), reference["compute_jac_daily_metrics"](old))
                for date in old["date"].unique():
                    assert_frame_equal(new.compute_command_latest_metrics(current, date),
                                       reference["compute_command_latest_metrics"](old, date))

    def test_edge_snapshots_and_formulas_match_both_references(self):
        cases = [
            pd.DataFrame({"date": ["2026-01-01 08:00", "2026-01-01 16:00", "2026-01-03 08:00"],
                          "tail": ["T", "T", "U"], "status": ["FMC", "NMCM", "mystery"],
                          "command": ["A", None, "B"], "hrs_to_insp": [20.0, np.nan, 30.0]}),
            pd.DataFrame({"date": ["2026-01-01"] * 2, "tail": ["T", "U"],
                          "status": ["NMCS", "DEPOT"], "command": ["A", "A"]}),
            pd.DataFrame({"date": ["bad"], "tail": ["T"], "status": ["FMC"]}),
            pd.DataFrame({"tail": ["T"]}),
        ]
        for name, reference in self.legacy.items():
            for number, raw in enumerate(cases):
                with self.subTest(reference=name, case=number), warnings.catch_warnings():
                    warnings.simplefilter("ignore", FutureWarning)
                    current = new.build_tail_daily_snapshot(raw)
                    old = reference["build_tail_daily_snapshot"](raw)
                    assert_frame_equal(current, old)
                    assert_frame_equal(new.compute_jac_daily_metrics(current), reference["compute_jac_daily_metrics"](old))
                    assert_frame_equal(new.compute_command_latest_metrics(current, "2026-01-01"),
                                       reference["compute_command_latest_metrics"](old, "2026-01-01"))

    def test_legacy_raw_duplicate_counting_defect_is_explicit(self):
        # Legacy total uses unique tails but numerator counts rows: 3 FMC rows / 2 tails.
        raw = pd.DataFrame({"date": pd.to_datetime(["2026-01-01"] * 3),
                            "tail": ["T", "T", "U"], "status": ["FMC"] * 3,
                            "command": ["A"] * 3})
        for name, reference in self.legacy.items():
            with self.subTest(reference=name):
                row = reference["compute_jac_daily_metrics"](raw).iloc[0]
                self.assertEqual(row["total_tails"], 2)
                self.assertEqual(row["svc_pct"], 150)
                self.assertEqual(reference["compute_command_latest_metrics"](raw, "2026-01-01").iloc[0]["avail_pct"], 150)
        with self.assertRaises(ValueError):
            new.compute_jac_daily_metrics(raw)


if __name__ == "__main__":
    unittest.main()
