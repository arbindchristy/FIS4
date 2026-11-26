"""Fictional dependency-independent scientific-preparation checks; no ML imports."""
from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
import tempfile
import unittest

from prediction.nmcs import Observation, reconstruct
from prediction.experiments import (Period, default_periods, validate_periods, references,
    prepare_example, SCHEMA, NUMERIC_FEATURES, CATEGORICAL_FEATURES, METHODS, STATES,
    fit_baselines, metrics, canonical_bytes, verify_manifest, clustered_brier_interval)


START = date(2020, 11, 21)


def observation(i, state='FMC', tail='000001'):
    return Observation(datetime.combine(START + timedelta(days=i), datetime.min.time()),
                       tail, state, 'FICTIONAL_A', 'UH-60L')


def fixture():
    return reconstruct([observation(i, STATES[i % 6]) for i in range(80)],
                       cutoff=observation(79).timestamp)


TRAIN = Period('train', START, START + timedelta(days=29))
VALIDATION = Period('validation', START + timedelta(days=30), START + timedelta(days=79))


class TemporalPreparationTests(unittest.TestCase):
    def test_four_chronological_partitions_and_overlap_rejection(self):
        validate_periods(default_periods())
        periods = list(default_periods())
        periods[1] = Period('validation', periods[0].end, periods[1].end)
        with self.assertRaises(ValueError):
            validate_periods(periods)

    def test_outcomes_are_purged_at_partition_end(self):
        examples = list(references(fixture(), VALIDATION, 7))
        self.assertEqual(examples[-1][1] + timedelta(days=7), VALIDATION.end)
        self.assertTrue(all(label.target_date <= VALIDATION.end for _, _, label in examples))
        self.assertTrue(all(day >= VALIDATION.start for _, day, _ in examples))

    def test_features_do_not_include_labels_or_future_inputs(self):
        h = fixture()
        day = START + timedelta(days=35)
        a = prepare_example(h, VALIDATION, '000001', day, 7)
        changed = reconstruct([observation(i, STATES[i % 6] if i <= 35 else 'NMCS') for i in range(80)],
                              cutoff=observation(79).timestamp)
        b = prepare_example(changed, VALIDATION, '000001', day, 7)
        self.assertEqual(a['numeric'], b['numeric'])
        self.assertEqual(a['categorical'], b['categorical'])
        self.assertEqual(a['schema'], SCHEMA)
        self.assertEqual(len(a['numeric']), len(NUMERIC_FEATURES))
        self.assertEqual(len(a['categorical']), len(CATEGORICAL_FEATURES))
        self.assertNotIn('tail', NUMERIC_FEATURES + CATEGORICAL_FEATURES)

    def test_missing_hours_and_insufficient_windows_remain_none(self):
        example = prepare_example(fixture(), VALIDATION, '000001', VALIDATION.start, 1)
        values = dict(zip(NUMERIC_FEATURES, example['numeric']))
        self.assertIsNone(values['hrs_to_insp'])
        self.assertIsNone(values['hrs_to_phase'])
        self.assertIsNone(values['nmcs_days_365'])

    def test_invalid_horizons_stride_and_outcome_boundary(self):
        for horizon in (0, 181, True):
            with self.assertRaises(ValueError):
                list(references(fixture(), VALIDATION, horizon))
        with self.assertRaises(ValueError):
            list(references(fixture(), VALIDATION, 1, stride_days=0))
        with self.assertRaises(ValueError):
            prepare_example(fixture(), VALIDATION, '000001', VALIDATION.end, 1)

    def test_nmcm_is_negative_and_current_nmcs_eligible(self):
        h = fixture()
        day = START + timedelta(days=33)  # Current NMCS -> NMCM next day.
        example = prepare_example(h, VALIDATION, '000001', day, 1)
        self.assertEqual(example['categorical'][0], 'NMCS')
        self.assertEqual(example['target'], 0)


class EmpiricalBaselineTests(unittest.TestCase):
    def test_training_is_deterministic(self):
        a = fit_baselines(fixture(), TRAIN)
        b = fit_baselines(fixture(), TRAIN)
        self.assertEqual(canonical_bytes(a.artifact()), canonical_bytes(b.artifact()))

    def test_future_outcomes_do_not_change_fitting(self):
        h = fixture()
        changed = reconstruct([observation(i, STATES[i % 6] if i < 30 else 'NMCS') for i in range(80)],
                              cutoff=observation(79).timestamp)
        self.assertEqual(fit_baselines(h, TRAIN), fit_baselines(changed, TRAIN))

    def test_all_methods_and_horizons_have_same_probability_contract(self):
        b = fit_baselines(fixture(), TRAIN)
        for method in METHODS:
            for horizon in range(1, 181):
                value = b.forecast(fixture(), '000001', VALIDATION.start, horizon, method)
                self.assertTrue(0 <= value['probability'] <= 1)
                self.assertEqual(value['target_date'], (VALIDATION.start + timedelta(days=horizon)).isoformat())
                self.assertIn('training_outcome_cutoff', value['explanation'])

    def test_empirical_occupancy_and_horizon_conditioned_recovery(self):
        b = fit_baselines(fixture(), TRAIN)
        self.assertAlmostEqual(b.predict('NMCS', 1, 'historical_occupancy'), 1 / 6)
        self.assertEqual(b.predict('NMCS', 1, 'persistence_recovery'), 0)
        self.assertEqual(b.predict('NMCS', 6, 'persistence_recovery'), 1)
        self.assertEqual(b.predict('NMCS', 1, 'transition_rule'), 0)

    def test_missing_support_falls_back_to_empirical_occupancy(self):
        h = reconstruct([observation(i) for i in range(80)], cutoff=observation(79).timestamp)
        b = fit_baselines(h, TRAIN)
        self.assertEqual(b.predict('NMCS', 180, 'persistence_recovery'), 0)
        for method in METHODS:
            self.assertEqual(b.predict('FMC', 7, method), 0)

    def test_in_sample_replay_and_missing_reference_rejected(self):
        b = fit_baselines(fixture(), TRAIN)
        with self.assertRaises(ValueError):
            b.forecast(fixture(), '000001', TRAIN.end, 7, METHODS[0])
        with self.assertRaises(ValueError):
            b.forecast(fixture(), 'unknown', VALIDATION.start, 7, METHODS[0])
        with self.assertRaises(ValueError):
            fit_baselines(fixture(), VALIDATION)

    def test_recovered_aircraft_not_excluded(self):
        rows = [observation(i, 'NMCS' if 20 <= i < 31 else 'FMC') for i in range(80)]
        h = reconstruct(rows, cutoff=observation(79).timestamp)
        b = fit_baselines(h, TRAIN)
        for day in (30, 31):
            for method in METHODS:
                self.assertTrue(0 <= b.forecast(h, '000001', START + timedelta(days=day), 7, method)['probability'] <= 1)


class ScientificEvidenceTests(unittest.TestCase):
    def test_metric_golden_examples(self):
        result = metrics([(1, .8), (1, .3), (0, .4), (0, .1)])
        self.assertAlmostEqual(result['brier'], .175)
        self.assertAlmostEqual(result['roc_auc'], .75)
        self.assertAlmostEqual(result['pr_auc_average_precision'], 5/6)
        self.assertEqual(result['prevalence'], .5)

    def test_tied_scores_and_single_class(self):
        result = metrics([(0, .5), (0, .5), (1, .5), (1, .5)])
        self.assertEqual(result['roc_auc'], .5)
        self.assertEqual(result['pr_auc_average_precision'], .5)
        self.assertEqual(result['top_decile_lift'], 1)
        self.assertEqual(result['ece_10_bins'], 0)
        self.assertIsNone(metrics([(0, 0.)])['roc_auc'])

    def test_machine_epsilon_is_not_predictive_ranking(self):
        result = metrics([(0, .5), (1, .5000000000000001)])
        self.assertEqual(result['roc_auc'], .5)
        self.assertEqual(result['pr_auc_average_precision'], .5)
        self.assertEqual(result['top_decile_lift'], 1)

    def test_invalid_probabilities_are_rejected(self):
        for pairs in ([], [(0, float('nan'))], [(1, 1.01)], [(2, .2)]):
            with self.assertRaises(ValueError):
                metrics(pairs)

    def test_cluster_bootstrap_is_deterministic_and_exposes_limits(self):
        rows = [{'tail': tail, 'reference_date': (START + timedelta(days=d)).isoformat(),
                 'outcome': d % 2, 'probability': .5}
                for tail in ('000001', '000002') for d in (0, 1, 35, 36)]
        a = clustered_brier_interval(rows, replicates=30)
        self.assertEqual(a, clustered_brier_interval(rows, replicates=30))
        self.assertEqual(a['lower'], .25)
        self.assertEqual(a['upper'], .25)
        self.assertIn('180-day', a['limitation'])
        self.assertIsNone(clustered_brier_interval(rows[:2]))

    def test_artifact_schema_provenance_and_integrity(self):
        root = Path(__file__).resolve().parents[1] / '.harness-test-tmp'
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            directory = Path(folder)
            paths = ('observations.csv', 'baselines.json', 'development_report.json')
            for path in paths:
                (directory / path).write_bytes(b'fictional-fixture\n')
            manifest = {'format': 'fis4-modeling-preparation-v1', 'feature_schema': SCHEMA,
                        'source': 'fictional_synthetic', 'source_revision': 'fictional-revision',
                        'sha256': {p: hashlib.sha256((directory / p).read_bytes()).hexdigest() for p in paths}}
            self.assertTrue(verify_manifest(directory, manifest))
            (directory / 'baselines.json').write_bytes(b'tampered')
            with self.assertRaises(ValueError):
                verify_manifest(directory, manifest)
            with self.assertRaises(ValueError):
                verify_manifest(directory, {**manifest, 'feature_schema': 'unknown'})
            with self.assertRaises(ValueError):
                verify_manifest(directory, {**manifest, 'source': 'operational'})


if __name__ == '__main__':
    unittest.main()
