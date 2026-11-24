"""Fictional exact-date occupancy, reconstruction and leakage regression tests."""
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta

from prediction.nmcs import Observation, reconstruct, features_at, target_at, label_coverage


START = date(2024, 1, 1)


def obs(offset, status='FMC', tail='000001', **kwargs):
    return Observation(datetime.combine(START + timedelta(days=offset), datetime.min.time()),
                       tail, status, kwargs.pop('command', 'FICTIONAL_A'),
                       kwargs.pop('platform', 'UH-60L'), **kwargs)


def history(rows, end=400, carry=False):
    return reconstruct(rows, cutoff=obs(end).timestamp, validated_reconstruction=carry)


class TargetTests(unittest.TestCase):
    def test_exact_dates_all_180_offsets(self):
        rows = [obs(i, 'NMCS' if i % 3 == 0 else 'NMCM') for i in range(181)]
        h = history(rows)
        for horizon in range(1, 181):
            with self.subTest(horizon=horizon):
                label = target_at(h, '000001', START, horizon)
                self.assertEqual(label.target_date, START + timedelta(days=horizon))
                self.assertEqual(label.value, int(horizon % 3 == 0))

    def test_not_any_onset_in_window(self):
        h = history([obs(0), obs(1, 'NMCS'), obs(2, 'NMCM')])
        self.assertEqual(target_at(h, '000001', START, 2).value, 0)

    def test_current_nmcs_remains_eligible(self):
        h = history([obs(0, 'NMCS'), obs(1, 'NMCS'), obs(2)])
        self.assertEqual(target_at(h, '000001', START, 1).value, 1)
        self.assertEqual(target_at(h, '000001', START, 2).value, 0)

    def test_every_non_nmcs_status_is_negative(self):
        for status in ['FMC', 'PMCM', 'PMCS', 'NMCM', 'DEPOT']:
            with self.subTest(status=status):
                self.assertEqual(target_at(history([obs(0), obs(1, status)]), '000001', START, 1).value, 0)

    def test_missing_target_is_not_negative(self):
        result = target_at(history([obs(0), obs(2)]), '000001', START, 1)
        self.assertIsNone(result.value)
        self.assertEqual(result.reason, 'target_unavailable')

    def test_validated_reconstruction_is_explicit(self):
        result = target_at(history([obs(0, 'NMCS'), obs(2)], carry=True), '000001', START, 1)
        self.assertEqual(result.value, 1)
        self.assertEqual(result.provenance, 'validated_carry')

    def test_future_cutoff_and_missing_tail(self):
        h = history([obs(0), obs(1, 'NMCS'), obs(2)], end=1)
        self.assertEqual(target_at(h, '000001', START, 2).reason, 'after_cutoff')
        self.assertEqual(target_at(h, '000099', START, 1).reason, 'reference_unavailable')

    def test_invalid_offsets_and_dates(self):
        h = history([obs(0), obs(1)])
        for horizon in [0, 181, True, 1.5, '7']:
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                target_at(h, '000001', START, horizon)
        with self.assertRaises(ValueError):
            target_at(h, '000001', datetime(2024, 1, 1), 1)

    def test_calendar_leap_day(self):
        h = history([obs(i) for i in range(62)])
        self.assertEqual(target_at(h, '000001', date(2024, 2, 28), 1).target_date, date(2024, 2, 29))

    def test_coverage_counts_match_individual_labels_with_gaps(self):
        h = history([obs(0), obs(2, 'NMCS'), obs(3, 'NMCM'), obs(4, 'NMCS')])
        report = label_coverage(h)
        for horizon in range(1, 181):
            labels = [target_at(h, '000001', START + timedelta(days=i), horizon) for i in range(5)]
            self.assertEqual(report[horizon]['eligible'], sum(l.value is not None for l in labels))
            self.assertEqual(report[horizon]['nmcs_positive'], sum(l.value == 1 for l in labels))


class ReconstructionTests(unittest.TestCase):
    def test_duplicate_identical_rows_and_order(self):
        a, b = obs(0), obs(1, 'NMCS')
        self.assertEqual(history([a, b]).by_tail, history([b, a, a]).by_tail)

    def test_conflicting_equal_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            history([obs(0), obs(0, 'NMCS')])

    def test_daily_last_and_independent_nonnull_hours(self):
        first = obs(0, hrs_to_insp=50, hrs_to_phase=150)
        later = replace(obs(0, 'PMCS', hrs_to_phase=140), timestamp=first.timestamp + timedelta(hours=12))
        row = history([later, first]).at('000001', START)
        self.assertEqual((row.status, row.hrs_to_insp, row.hrs_to_phase), ('PMCS', 50, 140))

    def test_readiness_parity_for_fictional_intraday_weekend_fixture(self):
        import pandas as pd
        import readiness
        rows = [obs(4, 'NMCS', hrs_to_insp=30),
                replace(obs(4, 'PMCS', hrs_to_phase=90), timestamp=obs(4).timestamp + timedelta(hours=14)),
                obs(7, 'NMCM')]
        raw = pd.DataFrame([{'date': r.timestamp, 'tail': r.tail, 'status': r.status,
                             'command': r.command, 'platform': r.platform,
                             'hrs_to_insp': r.hrs_to_insp, 'hrs_to_phase': r.hrs_to_phase} for r in rows])
        approved = readiness.build_tail_daily_snapshot(readiness.coalesce_columns(raw))
        actual = history(rows, carry=True).by_tail['000001']
        self.assertEqual([r.status for r in actual], approved.status.tolist())
        self.assertEqual([r.hrs_to_insp for r in actual], approved.hrs_to_insp.tolist())
        self.assertEqual([r.hrs_to_phase for r in actual], approved.hrs_to_phase.tolist())

    def test_gaps_do_not_become_fmc(self):
        row = history([obs(0, 'NMCS'), obs(3)]).at('000001', START + timedelta(days=1))
        self.assertEqual(row.status, 'NMCS')
        self.assertFalse(row.usable)
        self.assertFalse(row.observed)

    def test_no_backfill_or_extension_to_cutoff(self):
        h = history([obs(2), obs(4, tail='000002')], carry=True)
        self.assertIsNone(h.at('000001', START))
        self.assertIsNone(h.at('000001', START + timedelta(days=5)))
        self.assertIsNotNone(h.at('000001', START + timedelta(days=4)))

    def test_leading_zeros_and_independent_ownership(self):
        h = history([obs(0), obs(0, tail='000002', command='FICTIONAL_B', platform='AW139')])
        self.assertEqual(set(h.by_tail), {'000001', '000002'})
        self.assertEqual(h.at('000002', START).command, 'FICTIONAL_B')
        self.assertEqual(h.at('000001', START).platform, 'UH-60L')

    def test_ownership_changes_fail_closed(self):
        for field, value in [('command', 'FICTIONAL_B'), ('platform', 'AW139')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                history([obs(0), replace(obs(1), **{field: value})])

    def test_invalid_status_text_identity_hours_or_timezone(self):
        from datetime import timezone
        for row in [obs(0, 'NMC'), obs(0, 'UNKNOWN'), replace(obs(0), tail=1),
                    replace(obs(0), command=''), obs(0, hrs_to_phase=float('nan')),
                    replace(obs(0), timestamp=obs(0).timestamp.replace(tzinfo=timezone.utc))]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                history([row])

    def test_immutable_cache(self):
        h = history([obs(0)])
        with self.assertRaises(TypeError):
            h.by_tail['000002'] = ()

    def test_empty_input(self):
        h = history([])
        self.assertIsNone(target_at(h, '000001', START, 1).value)
        with self.assertRaises(ValueError):
            features_at(h, '000001', START)


class FeatureTests(unittest.TestCase):
    def test_future_records_do_not_change_features(self):
        rows = [obs(i, 'NMCS' if 2 <= i <= 4 else 'FMC', hrs_to_insp=40) for i in range(10)]
        future = [obs(i, 'NMCS', hrs_to_insp=9999) for i in range(10, 60)]
        self.assertEqual(features_at(history(rows), '000001', START + timedelta(days=9)),
                         features_at(history(rows + future), '000001', START + timedelta(days=9)))

    def test_invalid_future_values_after_cutoff_are_not_visible(self):
        rows = [obs(0), obs(1, 'NMCS')]
        future = replace(obs(2, 'INVALID'), command='FICTIONAL_B')
        self.assertEqual(history(rows, end=1), history(rows + [future], end=1))

    def test_persistent_nmcs_is_one_episode(self):
        rows = [obs(0)] + [obs(i, 'NMCS') for i in range(1, 5)] + [obs(5)]
        f = features_at(history(rows), '000001', START + timedelta(days=5), windows=(6,))
        self.assertEqual(f['nmcs_known_starts'], 1)
        self.assertEqual(f['completed_nmcs_durations'], (4,))
        self.assertEqual(f['windows'][6]['nmcs_days'], 4)
        self.assertEqual(f['days_since_last_nmcs'], 1)

    def test_gaps_censor_episodes_and_window_counts(self):
        rows = [obs(0), obs(1, 'NMCS'), obs(3, 'NMCS'), obs(4)]
        f = features_at(history(rows), '000001', START + timedelta(days=4), windows=(5,))
        self.assertIsNone(f['windows'][5]['nmcs_days'])
        self.assertEqual(f['windows'][5]['usable_days'], 4)
        self.assertEqual(f['nmcs_complete_episodes'], 0)
        self.assertEqual(f['nmcs_left_censored_fragments'], 1)

    def test_current_nmcs_state_and_censoring(self):
        f = features_at(history([obs(i, 'NMCS') for i in range(3)]), '000001', START + timedelta(days=2))
        self.assertEqual(f['days_since_last_nmcs'], 0)
        self.assertEqual(f['current_state_days_lower_bound'], 3)
        self.assertTrue(f['current_state_left_censored'])
        self.assertEqual(f['nmcs_complete_episodes'], 0)

    def test_missing_hours_and_no_previous_nmcs_are_explicit(self):
        f = features_at(history([obs(0)]), '000001', START)
        self.assertIsNone(f['hrs_to_insp'])
        self.assertIsNone(f['hrs_to_phase'])
        self.assertIsNone(f['days_since_last_nmcs'])
        self.assertTrue(f['hrs_to_phase_missing'])

    def test_complete_windows_30_90_180_365(self):
        rows = [obs(i, 'NMCS' if i % 2 == 0 else 'FMC') for i in range(365)]
        f = features_at(history(rows), '000001', START + timedelta(days=364))
        for window in (30, 90, 180, 365):
            with self.subTest(window=window):
                self.assertTrue(f['windows'][window]['complete'])
                self.assertEqual(f['windows'][window]['nmcs_days'], (window + 1) // 2)
        self.assertFalse(f['history_complete'])

    def test_recurrence_and_transition_statistics(self):
        rows = [obs(i, 'NMCS' if i in (1, 2, 5) else 'NMCM') for i in range(7)]
        f = features_at(history(rows), '000001', START + timedelta(days=6))
        self.assertEqual(f['completed_nmcs_durations'], (2, 1))
        self.assertEqual(f['completed_nmcs_duration_mean'], 1.5)
        self.assertEqual(f['nmcs_recurrence_interval_mean'], 4)
        self.assertEqual(f['state_transition_counts']['NMCS->NMCM'], 2)

    def test_feature_payload_has_no_tail_target_or_battalion(self):
        f = features_at(history([obs(0)]), '000001', START)
        for key in ('tail', 'target', 'label', 'battalion'):
            self.assertNotIn(key, f)

    def test_future_reference_unknown_tail_and_bad_windows_fail(self):
        h = history([obs(0)], end=0)
        for tail, day, args in [('000001', START + timedelta(days=1), {}),
                                 ('000002', START, {}), ('000001', START, {'windows': (True,)}),
                                 ('000001', START, {'history_years': 0})]:
            with self.subTest(tail=tail, args=args), self.assertRaises(ValueError):
                features_at(h, tail, day, **args)

    def test_uncovered_reference_does_not_use_future_global_end(self):
        rows = [obs(0), obs(5)]
        with self.assertRaises(ValueError):
            features_at(history(rows, carry=True), '000001', START + timedelta(days=3))

    def test_deterministic_feature_output(self):
        rows = [obs(i, 'NMCS' if i % 3 == 0 else 'PMCM') for i in range(31)]
        a = features_at(history(rows), '000001', START + timedelta(days=30))
        b = features_at(history(reversed(rows)), '000001', START + timedelta(days=30))
        self.assertEqual(a, b)

    def test_six_year_reference_is_explicit_and_never_backfilled(self):
        f = features_at(history([obs(0)]), '000001', START)
        self.assertEqual(f['requested_history_start'], '2018-01-02')
        self.assertEqual(f['effective_history_start'], START.isoformat())
        self.assertFalse(f['history_complete'])

    def test_recurrence_and_days_since_do_not_bridge_unknown_gaps(self):
        rows = [obs(0), obs(1, 'NMCS'), obs(2), obs(4), obs(5, 'NMCS'), obs(6)]
        h = history(rows)
        f = features_at(h, '000001', START + timedelta(days=6))
        self.assertIsNone(f['nmcs_recurrence_interval_mean'])
        at_four = features_at(h, '000001', START + timedelta(days=4))
        self.assertIsNone(at_four['days_since_last_nmcs'])
        self.assertEqual(at_four['days_since_last_known_nmcs'], 3)


if __name__ == '__main__':
    unittest.main()
