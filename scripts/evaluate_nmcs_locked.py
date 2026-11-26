"""Protocol v1.1 locked replay. Importing this module performs no data access."""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from importlib.metadata import version
from itertools import combinations
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prediction.experiments import METHODS, canonical_bytes
from prediction.ml_development import COLUMNS, HORIZONS, NUMERIC, feature_row, predict, score
from prediction.nmcs import features_at, reconstruct, target_at
from scripts.evaluate_nmcs_calibration import TMP, digest, load_baseline, verified_json

START = date(2025, 11, 21)
END = date(2026, 11, 20)
PRIMARY = (7, 30)
RECOVERY = 'persistence_recovery'
OCCUPANCY = 'historical_occupancy'
NAMES = (*METHODS, 'lr-c1_raw')
SEAL = '595c5c3bd4ad95dc33cc3e729b37b509ae2da6c6244397ac6ff66fe963ac01a3'
CAL_FREEZE = 'f8b1274636fe599f7f56057586f6fd9a23ef99c30bc8d82432b097d23739851d'
AUTHORIZATION = 'AUTHORIZE_ONE_TIME_PHASE05B_LOCKED_TEST_V1_1'


def require_authorization(path, freeze_hash):
    marker = json.loads(path.read_bytes())
    if (marker.get('authorization') != AUTHORIZATION
            or marker.get('freeze_sha256') != freeze_hash
            or marker.get('period') != [START.isoformat(), END.isoformat()]
            or not isinstance(marker.get('approval_reference'), str)
            or not marker['approval_reference'].strip()
            or not isinstance(marker.get('operator'), str)
            or not marker['operator'].strip()):
        raise ValueError('Explicit chief-architect authorization for this freeze is required')
    return marker


def verify_execution_authorization(marker_path, freeze_hash):
    marker = require_authorization(marker_path, freeze_hash)
    freeze = verified_json(TMP / 'phase05b-locked-v1.1-execution-freeze.json', freeze_hash)
    revision = freeze.get('git_head')
    if (not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision)
            or freeze.get('protocol') != '1.1' or freeze.get('calibration_seal_sha256') != SEAL):
        raise ValueError('Invalid execution freeze')
    head = subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'rev-parse', 'HEAD'],
        cwd=ROOT, text=True,
    ).strip()
    if head != revision:
        raise ValueError('HEAD differs from approved execution revision')
    required = {
        'docs/NMCS_MODELING.md', 'scripts/evaluate_nmcs_locked.py',
        'tests/test_nmcs_locked_evaluator.py', 'scripts/evaluate_nmcs_calibration.py',
        'prediction/nmcs.py', 'prediction/experiments.py', 'prediction/ml_development.py',
    }
    if set(freeze['source_sha256']) != required:
        raise ValueError('Incomplete execution source inventory')
    for name, expected in freeze['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Locked evaluator source changed: {name}')
    return marker


def verify_calibration():
    directory = TMP / 'phase05b-calibration-v1.1'
    seal = verified_json(directory / 'seal.json', SEAL)
    if (seal['comparator'], seal['coefficients'], seal['freeze_sha256']) != (
        'lr-c1_raw', None, CAL_FREEZE
    ):
        raise ValueError('Unexpected comparator seal')
    frozen = verified_json(TMP / 'phase05b-calibration-v1.1-freeze.json', CAL_FREEZE)
    for path, expected in frozen['source_sha256'].items():
        if digest(ROOT / path) != expected:
            raise ValueError(f'Calibration-frozen source changed: {path}')
    result = verified_json(directory / 'result.json', seal['result_sha256'])
    access = verified_json(directory / 'access.json', seal['access_sha256'])
    if (result['locked_test'] != 'NOT_RUN' or result['primary'] != RECOVERY
            or result['comparator'] != 'lr-c1_raw'
            or result['protocol_freeze_sha256'] != CAL_FREEZE
            or access['freeze_sha256'] != CAL_FREEZE):
        raise ValueError('Calibration result or access record is inconsistent')


def cohort(records, *, validated_reconstruction=True):
    cutoff = datetime.combine(END, time.max)
    if any(record.timestamp > cutoff for record in records):
        raise ValueError('Observation beyond the locked cutoff')
    history = reconstruct(records, cutoff=cutoff, validated_reconstruction=validated_reconstruction)
    exclusions = dict(calendar_purge=0, ineligible_reference=0, missing_target=0)
    roster = {'current_nmcs': {'NMCS', 'other'}, 'command': set(), 'platform': set()}
    for days in history.by_tail.values():
        roster['command'].add(days[0].command)
        roster['platform'].add(days[0].platform)
    rows = []
    for offset in range(0, (END - START).days + 1, 7):
        day = START + timedelta(days=offset)
        for tail in sorted(history.by_tail):
            if day + timedelta(days=max(HORIZONS)) > END:
                exclusions['calendar_purge'] += 1
                continue
            current = history.reference_at(tail, day)
            if current is None:
                exclusions['ineligible_reference'] += 1
                continue
            targets = [target_at(history, tail, day, h) for h in HORIZONS]
            if any(target.value is None for target in targets):
                exclusions['missing_target'] += 1
                continue
            raw = features_at(history, tail, day)
            for h, target in zip(HORIZONS, targets):
                if target.target_date != day + timedelta(days=h) or target.target_date > END:
                    raise ValueError('Invalid exact-date target')
                rows.append({
                    'date': day, 'tail': tail, 'horizon': h, 'target_date': target.target_date,
                    'label': target.value, 'state': current.status, 'command': current.command,
                    'platform': current.platform, 'features': feature_row(raw, h),
                })
    return rows, exclusions, roster


def support(rows, *, subgroup=False):
    counts = dict(rows=len(rows), positive=sum(r['label'] for r in rows),
                  tails=len({r['tail'] for r in rows}), dates=len({r['date'] for r in rows}))
    counts['negative'] = counts['rows'] - counts['positive']
    limits = (100, 20, 20, 20, 10) if subgroup else (1000, 50, 50, 100, 20)
    counts['adequate'] = all(counts[key] >= minimum for key, minimum in zip(
        ('rows', 'positive', 'negative', 'tails', 'dates'), limits))
    return counts


def losses(y, p):
    clipped = min(1 - 1e-15, max(1e-15, p))
    return (p - y) ** 2, -math.log(clipped if y else 1 - clipped)


def paired_interval(rows, horizon, method, reference):
    import numpy as np

    width = max(28, horizon)
    tails = {tail: i for i, tail in enumerate(sorted({r['tail'] for r in rows}))}
    block_dates = defaultdict(set)
    block_classes = defaultdict(set)
    for row in rows:
        block = (row['date'] - START).days // width
        block_dates[block].add(row['date'])
        block_classes[block].add(row['label'])
    qualifying = [b for b, days in block_dates.items() if len(days) >= 3]
    mixed = sum(len(block_classes[b]) == 2 for b in qualifying)
    info = dict(block_days=width, nonempty_blocks=len(block_dates),
                qualifying_blocks=len(qualifying), mixed_qualifying_blocks=mixed,
                brier_interval=None, log_loss_interval=None, nonzero_draws=0)
    if not support(rows)['adequate'] or len(qualifying) < 6 or mixed < 5:
        return dict(info, status='INCONCLUSIVE_INSUFFICIENT_SUPPORT')
    blocks = {b: i for i, b in enumerate(sorted(block_dates))}
    cells = np.zeros((len(tails), len(blocks), 3), dtype=float)
    for row in rows:
        cell = cells[tails[row['tail']], blocks[(row['date'] - START).days // width]]
        a = losses(row['label'], row['probabilities'][method])
        b = losses(row['label'], row['probabilities'][reference])
        cell += (1, a[0] - b[0], a[1] - b[1])
    rng = random.Random(42017)
    draws = []
    for _ in range(10_000):
        t = np.bincount(rng.choices(range(len(tails)), k=len(tails)), minlength=len(tails))
        b = np.bincount(rng.choices(range(len(blocks)), k=len(blocks)), minlength=len(blocks))
        total = np.einsum('i,j,ijc->c', t, b, cells)
        if total[0]:
            draws.append(total[1:] / total[0])
    info['nonzero_draws'] = len(draws)
    if len(draws) < 9500:
        return dict(info, status='INCONCLUSIVE_INSUFFICIENT_DRAWS')
    bounds = np.quantile(draws, [.025, .975], axis=0, method='linear')
    return dict(info, status='AVAILABLE', brier_interval=bounds[:, 0].tolist(),
                log_loss_interval=bounds[:, 1].tolist())


def metrics(rows, method, adequate):
    labels = [r['label'] for r in rows]
    probabilities = [r['probabilities'][method] for r in rows]
    result = score(labels, probabilities)
    result['signed_bias'] = (sum(probabilities) - sum(labels)) / len(rows)
    for entry in result['calibration']:
        bucket = entry['bin']
        positives = sum(y for y, p in zip(labels, probabilities) if min(9, int(10*p)) == bucket)
        entry.update(positive=positives, descriptive_only=entry['count'] < 50 or positives < 5)
    if not adequate:
        for key in ('roc_auc', 'pr_auc_average_precision', 'top_decile_lift',
                    'ece_10_bins', 'signed_bias', 'calibration'):
            result[key] = None
    by_date = defaultdict(lambda: [0.0, 0])
    for row, y, p in zip(rows, labels, probabilities):
        by_date[row['date']][0] += p
        by_date[row['date']][1] += y
    result['fleet_counts'] = [
        dict(date=day.isoformat(), expected=p, observed=y, absolute_error=abs(p-y))
        for day, (p, y) in sorted(by_date.items())
    ]
    result['count_mae'] = sum(r['absolute_error'] for r in result['fleet_counts']) / len(by_date)
    return result


def acceptance(overall, groups, interval, adequate):
    if not adequate:
        return dict(status='INCONCLUSIVE_NOT_VALIDATED', point_gain=False, harm=False)
    raw, ref = overall[RECOVERY], overall[OCCUPANCY]
    gain = ref['brier'] > 0 and raw['brier'] <= .98 * ref['brier']
    log_delta = raw['log_loss'] - ref['log_loss']
    bias, ece = abs(raw['signed_bias']), raw['ece_10_bins']
    harm = ((raw['brier'] > 0 and raw['brier'] >= 1.05 * ref['brier'])
            or log_delta > .010 or bias > .030 or ece > .040)
    checks = dict(brier_skill=gain, confidence=interval is not None and interval[1] < 0,
                  log_loss=log_delta <= .002, bias=bias <= .010, ece=ece <= .015,
                  subgroups=bool(groups) and all(g['guard_pass'] for g in groups))
    status = 'PASS' if all(checks.values()) and not harm else (
        'INCONCLUSIVE_NOT_VALIDATED' if interval is None or any(
            not g['support']['adequate'] for g in groups) else 'NOT_VALIDATED')
    return dict(status=status, point_gain=gain, harm=harm, checks=checks)


def evaluate(rows, roster):
    cohorts = defaultdict(list)
    keys = set()
    horizons_by_reference = defaultdict(set)
    for row in rows:
        key = row['date'], row['tail'], row['horizon']
        if key in keys or set(row['probabilities']) != set(NAMES):
            raise ValueError('Duplicate cohort key or method row mismatch')
        if (row['horizon'] not in HORIZONS or not START <= row['date'] <= END - timedelta(days=180)
                or (row['date'] - START).days % 7
                or row['target_date'] != row['date'] + timedelta(days=row['horizon'])
                or type(row['label']) is not int or row['label'] not in (0, 1)
                or any(not math.isfinite(p) or not 0 <= p <= 1
                       for p in row['probabilities'].values())):
            raise ValueError('Invalid cohort or prediction')
        keys.add(key)
        horizons_by_reference[key[:2]].add(key[2])
        cohorts[row['horizon']].append(row)
    if any(offsets != set(HORIZONS) for offsets in horizons_by_reference.values()):
        raise ValueError('Inconsistent horizon cohorts')
    report = {}
    for h in HORIZONS:
        selected = cohorts[h]
        counts = support(selected)
        overall = {m: metrics(selected, m, counts['adequate']) for m in NAMES} if selected else {}
        partitions = defaultdict(list)
        for row in selected:
            partitions['current_nmcs', 'NMCS' if row['state'] == 'NMCS' else 'other'].append(row)
            for field in ('command', 'platform'):
                partitions[field, row[field]].append(row)
        groups = []
        for field, values in roster.items():
            for value in sorted(values):
                members = partitions[field, value]
                evidence = support(members, subgroup=True)
                results = {m: metrics(members, m, evidence['adequate']) for m in NAMES} if members else {}
                passed = evidence['adequate'] and (
                    abs(results[RECOVERY]['signed_bias']) <= .030
                    and results[RECOVERY]['brier'] - results[OCCUPANCY]['brier'] <= .005)
                groups.append(dict(field=field, value=value, support=evidence,
                                   metrics=results, guard_pass=passed))
        contrasts = {}
        for method, ref in combinations((RECOVERY, 'lr-c1_raw', 'transition_rule', OCCUPANCY), 2):
            contrast = paired_interval(selected, h, method, ref)
            if selected:
                contrast.update(brier_delta=overall[method]['brier'] - overall[ref]['brier'],
                                log_loss_delta=overall[method]['log_loss'] - overall[ref]['log_loss'])
            contrasts[f'{method}_minus_{ref}'] = contrast
        key = f'{RECOVERY}_minus_{OCCUPANCY}'
        decision = acceptance(overall, groups, contrasts[key]['brier_interval'],
                              counts['adequate']) if h in PRIMARY else {'status': 'DESCRIPTIVE'}
        report[h] = dict(support=counts, metrics=overall, groups=groups,
                         contrasts=contrasts, decision=decision)
    primary = [report[h]['decision'] for h in PRIMARY]
    harm = any(item['harm'] for item in primary)
    qualified = [] if harm else [h for h in PRIMARY if report[h]['decision']['status'] == 'PASS']
    decision = ('FICTIONAL_LIMITED_HORIZON_PASS' if qualified else
                'EXPLORATORY_ONLY' if not harm and any(p['point_gain'] for p in primary) else 'NO_GO')
    return dict(horizons=report, decision=decision, validated_horizons=qualified,
                phase05c='NO_GO', family_alpha=.05, per_primary_one_sided_alpha=.025)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-sha256', required=True)
    parser.add_argument('--authorization-marker', required=True, type=Path)
    args = parser.parse_args()
    marker = verify_execution_authorization(args.authorization_marker, args.freeze_sha256)
    verify_calibration()
    runtime = verified_json(TMP / 'phase05b-runtime-qualification-v1/final-result.json',
                            'a8595076b43fb3bacf32bf7301c0714820ff12764dfc48e871c2c70561520c43')
    if (runtime['status'] != 'PASS' or sys.version_info[:3] != (3, 13, 7)
            or Path(sys.prefix).resolve() != (TMP / 'phase05b-ml-env').resolve()
            or any(version(k) != v for k, v in runtime['installed_versions'].items())):
        raise ValueError('Use the qualified scientific runtime')
    dataset = TMP / 'phase05b-six-year-42017-v3'
    models = TMP / 'phase05b-ml-development-v2'
    data_manifest = verified_json(dataset / 'manifest.json',
                                 'ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b')
    model_manifest = verified_json(models / 'manifest.json',
                                  '689b0f5e8a5d5bc100f090bb5820125a83c0fdcda10d4b0ee4b8990ee368c938')
    baseline = load_baseline(dataset / 'baselines.json', data_manifest['sha256']['baselines.json'])
    model_path = models / 'lr-c1.joblib'
    if digest(model_path) != model_manifest['sha256']['lr-c1.joblib']:
        raise ValueError('Unexpected comparator artifact')
    out = TMP / 'phase05b-locked-v1.1'
    out.mkdir(exist_ok=False)
    (out / 'access.json').write_bytes(canonical_bytes({
        'status': 'ATTEMPT_STARTED', 'authorization': marker, 'freeze_sha256': args.freeze_sha256,
        'dataset_sha256': data_manifest['sha256']['observations.csv'],
    }))
    try:
        import csv
        import io
        import hashlib
        import joblib
        import pandas as pd
        from prediction.nmcs import Observation

        # Hash and parse the same bytes, only after the exclusive access latch.
        payload = (dataset / 'observations.csv').read_bytes()
        if hashlib.sha256(payload).hexdigest() != data_manifest['sha256']['observations.csv']:
            raise ValueError('Observation export hash mismatch')
        reader = csv.DictReader(io.StringIO(payload.decode('utf-8'), newline=''))
        if reader.fieldnames != ['date', 'tail', 'status', 'command', 'platform']:
            raise ValueError('Unexpected observation schema')
        records = []
        last = None
        for record in reader:
            if None in record or any(value is None for value in record.values()):
                raise ValueError('Invalid observation row')
            stamp = datetime.fromisoformat(record['date'])
            key = stamp, record['tail']
            if stamp.date() > END or (last is not None and key <= last):
                raise ValueError('Invalid or duplicate chronological observation')
            records.append(Observation(stamp, record['tail'], record['status'],
                                       record['command'], record['platform']))
            last = key
        rows, exclusions, roster = cohort(records)
        if rows:
            frame = pd.DataFrame([r.pop('features') for r in rows], columns=COLUMNS)
            for name in NUMERIC:
                frame[name] = pd.to_numeric(frame[name], errors='raise').astype('float64')
            model_bytes = model_path.read_bytes()
            if hashlib.sha256(model_bytes).hexdigest() != model_manifest['sha256']['lr-c1.joblib']:
                raise ValueError('Comparator changed before loading')
            model = joblib.load(io.BytesIO(model_bytes))
            for row, value in zip(rows, predict(model, frame), strict=True):
                row['probabilities'] = {
                    m: baseline.predict(row['state'], row['horizon'], m) for m in METHODS
                }
                row['probabilities']['lr-c1_raw'] = float(value)
        report = evaluate(rows, roster)
        report.update(protocol='1.1', freeze_sha256=args.freeze_sha256, exclusions=exclusions,
                      scheduled_reference_dates=27, locked_period=[START.isoformat(), END.isoformat()])
        (out / 'predictions.jsonl').write_bytes(b''.join(canonical_bytes({
            **row, 'date': row['date'].isoformat(), 'target_date': row['target_date'].isoformat()
        }) for row in rows))
        (out / 'cohort.json').write_bytes(canonical_bytes([
            [row['date'].isoformat(), row['tail'], row['horizon']] for row in rows
        ]))
        (out / 'report.json').write_bytes(canonical_bytes(report))
        (out / 'execution.json').write_bytes(canonical_bytes({'status': 'COMPLETE'}))
    except Exception as error:
        (out / 'execution.json').write_bytes(canonical_bytes({
            'status': 'FAILED', 'decision': 'NO_GO', 'error_type': type(error).__name__,
        }))
        raise
    files = ('access.json', 'execution.json', 'report.json', 'predictions.jsonl', 'cohort.json')
    (out / 'manifest.json').write_bytes(canonical_bytes({name: digest(out / name) for name in files}))


if __name__ == '__main__':
    main()
