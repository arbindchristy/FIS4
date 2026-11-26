"""Prepare separate six-year fictional data and development baselines offline.

ML experiments stop when dependencies are absent; locked test is never scored.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prediction.nmcs import Observation, reconstruct, label_coverage, target_at
from prediction.experiments import (SCHEMA, METHODS, NUMERIC_FEATURES, CATEGORICAL_FEATURES,
    canonical_bytes, default_periods, validate_periods, fit_baselines, references,
    metrics, clustered_brier_interval, verify_manifest)
from simulator import generate, SimulationConfig

HORIZONS = (7, 14, 30, 45, 60, 90, 120, 123, 150, 180)


def distribution(values):
    values = sorted(values)
    if not values:
        return {'n': 0}
    return {'n': len(values), 'mean': statistics.mean(values), 'median': statistics.median(values),
            'min': values[0], 'max': values[-1],
            'p10': values[int((len(values)-1)*.1)], 'p90': values[int((len(values)-1)*.9)]}


def source_assessment(history):
    durations, recurrences = [], []
    runs = initial = ongoing = days = nmcs = 0
    for rows in history.by_tail.values():
        start = None
        previous_start = None
        censored = False
        for i, row in enumerate(rows):
            days += row.usable
            nmcs += row.usable and row.status == 'NMCS'
            if row.status == 'NMCS' and start is None:
                start = row.date
                censored = i == 0
                initial += censored
                runs += 1
                if previous_start:
                    recurrences.append((start - previous_start).days)
                previous_start = start
            elif row.status != 'NMCS' and start is not None:
                if not censored:
                    durations.append((row.date - start).days)
                start = None
        ongoing += start is not None
    window_support = dict.fromkeys((30, 90, 180, 365), 0)
    reference_days = 0
    for tail, rows in history.by_tail.items():
        missing = [0]
        for row in rows:
            missing.append(missing[-1] + int(not row.usable))
        for i, row in enumerate(rows):
            if history.reference_at(tail, row.date) is None:
                continue
            reference_days += 1
            for window in window_support:
                if i + 1 >= window and missing[i+1] == missing[i+1-window]:
                    window_support[window] += 1
    return {'usable_tail_days': days, 'nmcs_days': nmcs, 'nmcs_prevalence': nmcs / days,
            'nmcs_runs': runs, 'initial_left_censored': initial, 'ongoing_right_censored': ongoing,
            'completed_duration_days': distribution(durations),
            'start_to_start_recurrence_days': distribution(recurrences),
            'feature_completeness': {'eligible_reference_tail_days': reference_days,
                'complete_rolling_windows': window_support,
                'inspection_hours_present': 0, 'phase_hours_present': 0,
                'note': 'Event-only projection: both absent. No latent/operational joins or imputation.'},
            'eligible_by_horizon': label_coverage(history)}


def development_replay(history, baseline, period):
    # Predeclared common weekly references, purged for the longest horizon.
    cohort = [(tail, day) for tail, day, _ in references(history, period, 180, stride_days=7)
              if all(target_at(history, tail, day, h).value is not None for h in HORIZONS)]
    if not cohort:
        raise ValueError('No common development cohort')
    output = {}
    for horizon in HORIZONS:
        output[horizon] = {}
        for method in METHODS:
            rows = []
            for tail, day in cohort:
                result = baseline.forecast(history, tail, day, horizon, method)
                state = history.reference_at(tail, day)
                rows.append({'tail': tail, 'reference_date': day.isoformat(),
                             'outcome': target_at(history, tail, day, horizon).value,
                             'probability': result['probability'], 'command': state.command,
                             'platform': state.platform, 'already_nmcs': state.status == 'NMCS'})
            report = metrics((r['outcome'], r['probability']) for r in rows)
            report['brier_cluster_interval'] = clustered_brier_interval(rows)
            report['current_nmcs_groups'] = {str(flag): metrics(
                (r['outcome'], r['probability']) for r in rows if r['already_nmcs'] == flag)
                for flag in (True, False) if any(r['already_nmcs'] == flag for r in rows)}
            for field in ('command', 'platform'):
                groups = {}
                for value in sorted({r[field] for r in rows}):
                    group = [r for r in rows if r[field] == value]
                    positives = sum(r['outcome'] for r in group)
                    groups[value] = (metrics((r['outcome'], r['probability']) for r in group)
                                     if len(group) >= 100 and min(positives, len(group)-positives) >= 10
                                     else {'n': len(group), 'positive': positives,
                                           'status': 'insufficient_class_support'})
                report[field + '_groups'] = groups
            fleet = defaultdict(lambda: [0., 0, 0])
            for r in rows:
                fleet[r['reference_date']][0] += r['probability']
                fleet[r['reference_date']][1] += r['outcome']
                fleet[r['reference_date']][2] += 1
            report['fleet_counts'] = {'dates': len(fleet),
                'mean_expected': statistics.mean(v[0] for v in fleet.values()),
                'mean_observed': statistics.mean(v[1] for v in fleet.values()),
                'mean_absolute_count_error': statistics.mean(abs(v[0]-v[1]) for v in fleet.values()),
                'cohort_sizes': sorted({v[2] for v in fleet.values()})}
            output[horizon][method] = report
    return {'kind': 'model_development_validation_only', 'stride_days': 7,
            'common_examples_per_horizon': len(cohort),
            'reference_start': min(day for _, day in cohort).isoformat(),
            'reference_end': max(day for _, day in cohort).isoformat(),
            'horizons': output,
            'limitations': 'No ML comparison, calibrator, locked-test scores or in-sample metrics. '
                           'Weekly overlap and a small number of time blocks limit interval precision.'}


def main():
    parser = argparse.ArgumentParser(description='Offline fictional preparation; no ML dependencies installed')
    parser.add_argument('--output-name', default='phase05b-six-year-42017-v1')
    parser.add_argument('--reuse-dataset', help='Verified own workspace experiment name; avoids regeneration')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.output_name):
        parser.error('Workspace-local artifact name required')
    destination = ROOT / '.harness-test-tmp' / args.output_name
    if destination.exists():
        parser.error('Refusing to overwrite an existing experiment')
    periods = default_periods()
    validate_periods(periods)
    started = time.perf_counter()
    config = SimulationConfig(as_of=date(2026, 11, 20), seed=42017, years=6)
    reused_manifest_hash = None
    if args.reuse_dataset:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', args.reuse_dataset):
            parser.error('Workspace-local source experiment name required')
        source = ROOT / '.harness-test-tmp' / args.reuse_dataset
        original = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
        verify_manifest(source, original)
        if original['config'] != {'seed': config.seed, 'years': config.years, 'tails': config.tails,
                                  'start': config.start.isoformat(), 'end': config.as_of.isoformat(),
                                  'days': config.days}:
            raise ValueError('Source dataset configuration mismatch')
        for path in ('simulator/generator.py', 'simulator/contracts.py', 'readiness.py'):
            if original['source_sha256'][path] != hashlib.sha256((ROOT / path).read_bytes()).hexdigest():
                raise ValueError('Source generation revision mismatch')
        import pandas as pd
        events = pd.read_csv(source / 'observations.csv', dtype=str, keep_default_na=False)
        events['date'] = pd.to_datetime(events['date'], format='%Y-%m-%dT%H:%M:%S')
        reused_manifest_hash = hashlib.sha256((source / 'manifest.json').read_bytes()).hexdigest()
    else:
        world = generate(config)
        events = world.events
    history = reconstruct((Observation(r.date.to_pydatetime(), r.tail, r.status, r.command, r.platform)
                           for r in events.itertuples(index=False)),
                          cutoff=events.date.max().to_pydatetime(), validated_reconstruction=True)
    coverage = source_assessment(history)
    baseline = fit_baselines(history, periods[0])
    replay = development_replay(history, baseline, periods[1])
    dependencies = {}
    for name in ('numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib', 'threadpoolctl'):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    report = {'source': 'fictional_synthetic', 'config': {'seed': config.seed, 'years': config.years,
              'tails': config.tails, 'start': config.start.isoformat(), 'end': config.as_of.isoformat(),
              'days': config.days},
              'commands': dict(Counter(rows[0].command for rows in history.by_tail.values())),
              'platforms': dict(Counter(rows[0].platform for rows in history.by_tail.values())),
              'coverage': coverage, 'development_replay': replay, 'dependencies': dependencies,
              'candidate_ml': {'logistic_regression': 'BLOCKED_missing_scikit_learn',
                               'gradient_boosted_tree': 'BLOCKED_missing_scikit_learn'},
              'calibration': 'NOT_FITTED_reserved_partition',
              'locked_test': 'NOT_EVALUATED_model_selection_incomplete',
              'phase05c': 'NO_GO_incomplete_ML_and_locked_out_of_time_validation',
              'elapsed_seconds': round(time.perf_counter() - started, 3)}
    destination.mkdir(parents=True, exist_ok=False)
    events.to_csv(destination / 'observations.csv', index=False, lineterminator='\n',
                        date_format='%Y-%m-%dT%H:%M:%S')
    (destination / 'baselines.json').write_bytes(canonical_bytes(baseline.artifact()))
    (destination / 'development_report.json').write_bytes(canonical_bytes(report))
    revision = subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT.as_posix(),
        '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    source_files = ('simulator/generator.py', 'simulator/contracts.py', 'readiness.py',
                    'prediction/nmcs.py', 'prediction/experiments.py', 'scripts/prepare_nmcs_modeling.py')
    manifest = {'format': 'fis4-modeling-preparation-v1', 'source': 'fictional_synthetic',
        'source_revision': revision, 'feature_schema': SCHEMA,
        'numeric_feature_order': NUMERIC_FEATURES, 'categorical_feature_order': CATEGORICAL_FEATURES,
        'source_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_files},
        'partitions': [{'name': p.name, 'start': p.start.isoformat(), 'end': p.end.isoformat()} for p in periods],
        'config': report['config'], 'python': sys.version.split()[0], 'dependencies': dependencies,
        'evaluation_id': args.output_name + '-development-only', 'seed': config.seed,
        'reused_dataset_manifest_sha256': reused_manifest_hash,
        'ml_artifact': None, 'training_code_state': 'base_revision_plus_exact_source_hashes',
        'sha256': {p: hashlib.sha256((destination / p).read_bytes()).hexdigest()
                   for p in ('observations.csv', 'baselines.json', 'development_report.json')}}
    verify_manifest(destination, manifest)
    (destination / 'manifest.json').write_bytes(canonical_bytes(manifest))
    print(json.dumps({'artifact_directory': str(destination.relative_to(ROOT)),
                      'elapsed_seconds': report['elapsed_seconds'], 'phase05c': report['phase05c'],
                      'manifest_sha256': hashlib.sha256(canonical_bytes(manifest)).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
