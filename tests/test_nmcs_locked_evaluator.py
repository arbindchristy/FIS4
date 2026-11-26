from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from prediction.nmcs import Observation
from scripts import evaluate_nmcs_locked as locked


def observation(day, status):
    return Observation(datetime.combine(day, locked.time()), '00001', status, 'Fictional', 'Demo')


class LockedEvaluatorTests(unittest.TestCase):
    def test_frozen_calibration_seal(self):
        locked.verify_calibration()

    def test_marker_and_hash_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=locked.TMP) as folder:
            marker = Path(folder) / 'marker.json'
            with self.assertRaises(FileNotFoundError):
                locked.require_authorization(marker, 'reviewed')
            marker.write_text('{"authorization":"WRONG"}', encoding='utf-8')
            with self.assertRaises(ValueError):
                locked.require_authorization(marker, 'reviewed')
            with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
                locked.verified_json(marker, 'wrong')

    def test_leakage_rejected_and_later_targets_do_not_change_features(self):
        start = locked.START
        rows = [observation(start, 'FMC'),
                observation(start + timedelta(days=180), 'NMCS')]
        a, _, _ = locked.cohort(rows)
        b, _, _ = locked.cohort([rows[0], observation(start + timedelta(days=180), 'NMCM')])
        self.assertEqual([r['features'] for r in a], [r['features'] for r in b])
        self.assertEqual((a[-1]['label'], b[-1]['label']), (1, 0))
        with self.assertRaisesRegex(ValueError, 'beyond'):
            locked.cohort(rows + [observation(locked.END + timedelta(days=1), 'NMCS')])

    def test_missing_target_and_fleet_observation_exclusions(self):
        rows, excluded, _ = locked.cohort([observation(locked.START, 'FMC')])
        self.assertFalse(rows)
        self.assertEqual(excluded['missing_target'], 1)
        self.assertEqual(excluded['ineligible_reference'], 26)
        self.assertGreater(excluded['calendar_purge'], 0)

    def test_identical_cohorts_and_inconclusive_report(self):
        rows, _, roster = locked.cohort([
            observation(locked.START, 'FMC'),
            observation(locked.START + timedelta(days=180), 'NMCS'),
        ])
        for row in rows:
            row['probabilities'] = dict.fromkeys(locked.NAMES, .2)
        result = locked.evaluate(rows, roster)
        self.assertEqual(result['decision'], 'NO_GO')
        self.assertEqual(result['horizons'][7]['decision']['status'],
                         'INCONCLUSIVE_NOT_VALIDATED')
        with self.assertRaisesRegex(ValueError, 'Inconsistent'):
            locked.evaluate(rows[:-1], roster)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            locked.evaluate(rows + rows[:1], roster)

    def test_gates_and_failed_thresholds(self):
        ref = dict(brier=.10, log_loss=.40)
        raw = dict(brier=.09, log_loss=.401, signed_bias=.005, ece_10_bins=.010)
        overall = {locked.RECOVERY: raw, locked.OCCUPANCY: ref}
        subgroup = [dict(guard_pass=True, support=dict(adequate=True))]
        self.assertEqual(locked.acceptance(overall, subgroup, [-.02, -.01], True)['status'], 'PASS')
        self.assertEqual(locked.acceptance(overall, subgroup, None, True)['status'],
                         'INCONCLUSIVE_NOT_VALIDATED')
        self.assertEqual(locked.acceptance(overall, subgroup, [-.02, .001], True)['status'],
                         'NOT_VALIDATED')
        raw['log_loss'] = .403
        self.assertFalse(locked.acceptance(overall, subgroup, [-.02, -.01], True)['checks']['log_loss'])
        raw['signed_bias'] = .031
        self.assertTrue(locked.acceptance(overall, subgroup, [-.02, -.01], True)['harm'])

    def test_paired_inference_respects_support_and_delta_sign(self):
        rows = []
        for week in range(26):
            for tail in range(100):
                label = tail % 2
                rows.append(dict(date=locked.START + timedelta(days=week*7),
                                 tail=str(tail), label=label,
                                 probabilities={locked.RECOVERY: .8 if label else .2,
                                                locked.OCCUPANCY: .5}))
        point = locked.paired_interval(rows, 7, locked.RECOVERY, locked.OCCUPANCY)
        self.assertEqual(point['nonzero_draws'], 10000)
        self.assertAlmostEqual(point['brier_interval'][1], -.21)
        self.assertIsNone(locked.paired_interval(rows, 180, locked.RECOVERY,
                                                locked.OCCUPANCY)['brier_interval'])


if __name__ == '__main__':
    unittest.main()
