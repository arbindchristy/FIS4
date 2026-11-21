"""Portable integrity tests: fictional generator only, no SQL or network access."""
from copy import deepcopy
from datetime import date
import hashlib
import random
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

import readiness
from simulator import SimulationConfig, generate
from simulator.contracts import COMMANDS, SCHEMAS


def digest(history):
    result = hashlib.sha256()
    for name in (*SCHEMAS, "snapshot"):
        result.update(getattr(history, name).to_csv(index=False, lineterminator="\n").encode())
    return result.hexdigest()


def set_column(history, table, column, value):
    frame = getattr(history, table)
    frame[column] = value


class SimulatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = SimulationConfig(date(2026, 11, 20))
        cls.history = generate(cls.config)
        cls.small_config = SimulationConfig(date(2024, 2, 29), tails=8, years=1)
        cls.small = generate(cls.small_config)

    def test_default_population_and_complete_calendar_coverage(self):
        h = self.history
        self.assertEqual(len(h.aircraft), 160)
        self.assertEqual(h.aircraft["tail"].nunique(), 160)
        self.assertEqual(set(h.aircraft.command), set(COMMANDS))
        self.assertEqual(h.aircraft.groupby("command").size().tolist(), [40] * 4)
        self.assertEqual(h.config.start, date(2022, 11, 21))
        self.assertEqual(len(h.operations), 160 * 1461)
        self.assertEqual(h.operations.groupby("tail").size().unique().tolist(), [1461])
        self.assertEqual(set(h.snapshot.status), set(readiness.CANONICAL_STATUSES))

    def test_repeated_full_generation_has_identical_tables_and_bytes(self):
        other = generate(self.config)
        for name in (*SCHEMAS, "snapshot"):
            assert_frame_equal(getattr(self.history, name), getattr(other, name))
        self.assertEqual(digest(self.history), digest(other))

    def test_other_seed_changes_valid_history(self):
        other = generate(SimulationConfig(date(2024, 2, 29), seed=19, tails=8, years=1))
        other.validate()
        self.assertNotEqual(digest(self.small), digest(other))

    def test_leap_cutoff_and_configuration_bounds(self):
        self.assertEqual(self.small_config.start, date(2023, 3, 1))
        self.assertEqual(self.small_config.days, 366)
        for kwargs in ({"tails": 159}, {"tails": True}, {"tails": 0}, {"years": 0},
                       {"years": 11}, {"seed": -1}, {"seed": True},
                       {"tails": 1600, "years": 10}, {"as_of": "2026-11-20"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate(SimulationConfig(**({"as_of": date(2026, 11, 20)} | kwargs)))

    def test_local_rng_does_not_modify_global_random_state(self):
        before = random.getstate()
        generate(self.small_config)
        self.assertEqual(random.getstate(), before)

    def test_provider_copy_leading_zero_identifiers_and_engine_reuse(self):
        h = self.small
        events = h.load_events()
        self.assertEqual(h.source, "synthetic")
        self.assertEqual(events["tail"].iloc[0], "000001")
        events.loc[0, "status"] = "INVALID"
        self.assertNotEqual(h.events.loc[0, "status"], "INVALID")
        rebuilt = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(h.load_events()))
        assert_frame_equal(h.snapshot, rebuilt.sort_values(["date", "tail"]).reset_index(drop=True))

    def test_command_fleet_reconciliation_uses_existing_engine(self):
        h = self.history
        fleet = readiness.compute_jac_daily_metrics(h.snapshot)
        for day in (fleet.date.min(), fleet.date.iloc[len(fleet) // 2], fleet.date.max()):
            commands = readiness.compute_command_latest_metrics(h.snapshot, day)
            fleet_row = fleet[fleet.date.eq(day)].iloc[0]
            self.assertEqual(len(commands), 4)
            for field in ("total_tails", "fmc_tails", "pmc_tails", "nmcs_tails", "nmcm_tails", "depot_tails"):
                self.assertEqual(commands[field].sum(), fleet_row[field])

    def test_flights_accumulate_and_grounded_aircraft_do_not_fly(self):
        h = self.history
        daily = h.operations.merge(h.snapshot, on=["date", "tail"])
        self.assertTrue(daily[daily.status.isin(["NMCS", "NMCM", "DEPOT"])].flight_hours.eq(0).all())
        initial = h.operations["tail"].map(h.aircraft.set_index("tail").initial_hours)
        self.assertTrue((h.operations.groupby("tail").flight_hours.cumsum() + initial
                         - h.operations.total_hours).abs().lt(1e-7).all())
        self.assertTrue(h.operations.flight_hours.gt(0).any())

    def test_inspections_and_depot_have_persistent_causal_lifecycles(self):
        h = self.history
        self.assertTrue({"INSPECTION", "DEPOT", "FAULT"}.issubset(set(h.episodes.kind)))
        self.assertTrue(h.operations.hrs_to_insp.eq(0).any())
        self.assertTrue(h.episodes.closed_at.isna().any())  # Right-censored at as-of.
        for kind, minimum in (("INSPECTION", 2), ("DEPOT", 30)):
            done = h.episodes[h.episodes.kind.eq(kind) & h.episodes.closed_at.notna()]
            self.assertTrue((done.closed_at - done.opened_at).dt.days.ge(minimum - 1).all())

    def test_supply_timing_and_recurrence_are_observed_not_future_features(self):
        h = self.history
        timeline = h.actions.pivot(index="episode_id", columns="action", values="date")
        received = timeline[timeline.PART_RECEIPT.notna()]
        self.assertGreater(len(received), 0)
        self.assertTrue(received.PART_RECEIPT.gt(received.PART_REQUEST).all())
        completed = received[received.CLOSE.notna()]
        self.assertTrue(completed.CLOSE.gt(completed.PART_RECEIPT).all())
        self.assertTrue(h.episodes.recurring.any())
        self.assertTrue(h.operations.outstanding_demand.eq(1).any())
        self.assertTrue(h.operations.supply_wait_days.gt(1).any())

    def test_features_at_cutoff_cannot_read_future_outcomes(self):
        h = deepcopy(self.small)
        cutoff = h.config.start
        before = h.features_at(cutoff)
        h.episodes.loc[:, "closed_at"] = pd.Timestamp("2099-01-01")
        h.actions.loc[:, "date"] = pd.Timestamp("2099-01-01")
        h.operations.loc[h.operations.date.gt(pd.Timestamp(cutoff)), "fault_count"] = 999
        assert_frame_equal(before, h.features_at(cutoff))
        self.assertFalse({"closed_at", "PART_RECEIPT", "duration", "arrival"} & set(before))
        with self.assertRaises(ValueError):
            h.features_at(date(2001, 1, 1))

    def test_command_conditions_have_different_nontrivial_outcomes(self):
        h = self.history
        joined = h.operations.merge(h.snapshot, on=["date", "tail"])
        means = joined.groupby("command").flight_hours.mean()
        self.assertGreater(means.max() - means.min(), .1)
        # Both outcomes occur under every command; assumptions are not labels.
        for _, group in joined.groupby("command"):
            self.assertTrue(group.status.eq("FMC").any())
            self.assertTrue(group.status.eq("NMCS").any())
            self.assertTrue(group.status.eq("NMCM").any())

    def rejected(self, mutate):
        h = deepcopy(self.small)
        mutate(h)
        with self.assertRaises(ValueError):
            h.validate()

    def test_reject_conflicting_events_and_unknown_status(self):
        self.rejected(lambda h: setattr(h, "events", pd.concat([h.events, h.events.iloc[[0]]], ignore_index=True)))
        self.rejected(lambda h: set_column(h, "events", "status", "UNKNOWN"))

    def test_reject_missing_day_or_tail(self):
        self.rejected(lambda h: setattr(h, "operations", h.operations.iloc[1:].reset_index(drop=True)))
        self.rejected(lambda h: set_column(h, "aircraft", "tail", "1"))

    def test_reject_bad_order_snapshot_and_command(self):
        self.rejected(lambda h: setattr(h, "events", h.events.iloc[::-1].reset_index(drop=True)))
        self.rejected(lambda h: set_column(h, "snapshot", "status", "FMC"))
        self.rejected(lambda h: set_column(h, "events", "command", "FICTIONAL_WRONG"))

    def test_reject_corrupt_accumulated_or_inspection_hours(self):
        self.rejected(lambda h: set_column(h, "operations", "total_hours", h.operations.total_hours + 1))
        self.rejected(lambda h: set_column(h, "operations", "hrs_to_insp", 10.0))

    def test_reject_causally_invalid_supply_action(self):
        def mutate(h):
            mask = h.actions.action.eq("PART_RECEIPT")
            h.actions.loc[mask, "date"] = pd.Timestamp(h.config.start)
            h.actions = h.actions.sort_values(["date", "episode_id", "action"]).reset_index(drop=True)
        self.rejected(mutate)

    def test_reject_hidden_active_episode_and_future_action(self):
        self.rejected(lambda h: set_column(h, "operations", "active_episode", ""))
        self.rejected(lambda h: set_column(h, "actions", "date", pd.Timestamp("2099-01-01")))

    def test_reject_corrupt_past_fault_features(self):
        self.rejected(lambda h: set_column(h, "operations", "fault_count", 0))
        self.rejected(lambda h: set_column(h, "operations", "outstanding_demand", 0))


if __name__ == "__main__":
    unittest.main()
