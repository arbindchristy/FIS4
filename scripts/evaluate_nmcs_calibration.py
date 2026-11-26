"""Frozen Phase 05B v1.1 calibration-only replay for the unsupported-fold path."""
import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta
from hashlib import file_digest, sha256
from importlib.metadata import version
import json
from pathlib import Path
from statistics import mean
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prediction.experiments import EmpiricalBaselines, canonical_bytes
from prediction.ml_development import score
from prediction.nmcs import Observation, reconstruct, target_at

START = date(2024, 11, 21)
END = date(2025, 11, 20)
HORIZONS = (7, 30)
FOLDS = (
    (date(2025, 2, 28), date(2025, 3, 1), date(2025, 4, 30)),
    (date(2025, 4, 30), date(2025, 5, 1), date(2025, 7, 31)),
    (date(2025, 7, 31), date(2025, 8, 1), END),
)
HEAD = 'b3a44198ddf11526c27bfe8676bb42339e4f900d'
TMP = ROOT / '.harness-test-tmp'
FREEZE = TMP / 'phase05b-calibration-v1.1-freeze.json'
HEADER = b'date,tail,status,command,platform\n'


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def verified_json(path, expected):
    if digest(path) != expected:
        raise ValueError(f'Hash mismatch for {path.name}')
    return json.loads(path.read_bytes())


def prefix(path, cutoff):
    """Consume a sorted export through cutoff; inspect only the next date field."""
    records = []
    fingerprint = sha256()
    with path.open('rb', buffering=0) as stream:
        if stream.readline() != HEADER:
            raise ValueError('Unexpected observation header')
        fingerprint.update(HEADER)
        previous = None
        while field := stream.read(10):
            day = date.fromisoformat(field.decode('ascii'))
            if day > cutoff:
                break
            line = field + stream.readline()
            timestamp, tail, status, command, platform = line.decode('utf-8').rstrip('\r\n').split(',')
            stamp = datetime.fromisoformat(timestamp)
            key = stamp, tail
            if stamp.date() != day or (previous is not None and key <= previous):
                raise ValueError('Invalid or duplicate chronological observation')
            previous = key
            records.append(Observation(stamp, tail, status, command, platform))
            fingerprint.update(line)
        else:
            raise ValueError('Expected end-of-partition boundary')
    return records, fingerprint.hexdigest()


def grid(start, end):
    return [START + timedelta(days=i) for i in range(0, (end - START).days + 1, 7)
            if START + timedelta(days=i) >= start]


def block_counts(dates, anchor):
    return Counter((day - anchor).days // 30 for day in dates)


def cohort(records, start, end):
    history = reconstruct(records, cutoff=datetime.combine(end, time.max),
                          validated_reconstruction=True)
    excluded = Counter(calendar_purge=0, ineligible_reference=0, missing_target=0)
    rows = []
    for day in grid(start, end):
        for tail in sorted(history.by_tail):
            if day + timedelta(days=max(HORIZONS)) > end:
                excluded['calendar_purge'] += 1
                continue
            reference = history.reference_at(tail, day)
            if reference is None:
                excluded['ineligible_reference'] += 1
                continue
            outcomes = [target_at(history, tail, day, h) for h in HORIZONS]
            if any(item.value is None for item in outcomes):
                excluded['missing_target'] += 1
                continue
            rows.append((day, tail, reference, outcomes))
    return rows, dict(excluded)


def summary(rows, anchor):
    dates = sorted({day for day, *_ in rows})
    blocks = block_counts(dates, anchor)
    result = {}
    for index, horizon in enumerate(HORIZONS):
        classes = {}
        positives = 0
        for day, _, _, targets in rows:
            value = targets[index].value
            positives += value
            classes.setdefault((day - anchor).days // 30, set()).add(value)
        result[horizon] = {
            'rows': len(rows), 'positive': positives, 'negative': len(rows) - positives,
            'reference_dates': len(dates), 'distinct_tails': len({row[1] for row in rows}),
            'blocks': dict(blocks), 'blocks_with_three_dates': sum(n >= 3 for n in blocks.values()),
            'qualifying_mixed_blocks': sum(blocks[k] >= 3 and len(v) == 2 for k, v in classes.items()),
        }
    return result


def load_baseline(path, expected):
    raw = verified_json(path, expected)
    if (raw['source'], raw['target'], raw['training_outcome_cutoff']) != (
        'fictional_synthetic', 'NMCS_occupancy_at_T_plus_H', '2023-11-20'
    ):
        raise ValueError('Unexpected baseline contract')
    return EmpiricalBaselines(
        date.fromisoformat(raw['training_start']), date.fromisoformat(raw['training_outcome_cutoff']),
        tuple(raw['state_counts']), tuple(map(tuple, raw['transition_counts'])),
        tuple(tuple(map(tuple, rows)) for rows in raw['horizon_counts']),
        tuple(map(tuple, raw['transition_probabilities'])),
    )


def recovery_report(rows, baseline):
    result = {}
    for i, h in enumerate(HORIZONS):
        by_date = {}
        pairs = []
        for day, _, reference, targets in rows:
            label = targets[i].value
            prob = baseline.predict(reference.status, h, 'persistence_recovery')
            pairs.append((label, prob))
            daily = by_date.setdefault(day, [0, 0.0])
            daily[0] += label
            daily[1] += prob
        result[h] = score(*zip(*pairs))
        result[h].update(
            mean_probability=mean(p for _, p in pairs),
            signed_bias=mean(p - y for y, p in pairs),
            expected_count=mean(p for _, p in by_date.values()),
            observed_count=mean(y for y, _ in by_date.values()),
            count_mae=mean(abs(p - y) for y, p in by_date.values()),
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    freeze = verified_json(FREEZE, args.freeze_sha256)
    if freeze['git_head'] != HEAD or subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT.as_posix()}', 'rev-parse', 'HEAD'],
        cwd=ROOT, text=True,
    ).strip() != HEAD:
        raise ValueError('Unexpected source revision')
    for name, expected in freeze['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen source changed: {name}')
    runtime = verified_json(TMP / 'phase05b-runtime-qualification-v1/final-result.json',
                            'a8595076b43fb3bacf32bf7301c0714820ff12764dfc48e871c2c70561520c43')
    if (runtime['status'] != 'PASS' or sys.version_info[:3] != (3, 13, 7)
            or Path(sys.prefix).resolve() != (TMP / 'phase05b-ml-env').resolve()
            or any(version(k) != v for k, v in runtime['installed_versions'].items())):
        raise ValueError('Isolated runtime differs from qualification')
    dataset = TMP / 'phase05b-six-year-42017-v3'
    models = TMP / 'phase05b-ml-development-v2'
    data_manifest = verified_json(dataset / 'manifest.json',
                                 'ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b')
    model_manifest = verified_json(models / 'manifest.json',
                                  '689b0f5e8a5d5bc100f090bb5820125a83c0fdcda10d4b0ee4b8990ee368c938')
    for name in ('lr-c1.joblib', 'frozen_candidate.json'):
        if digest(models / name) != model_manifest['sha256'][name]:
            raise ValueError(f'Comparator artifact mismatch: {name}')
    for name, expected in model_manifest['working_source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Development source mismatch: {name}')
    baseline = load_baseline(dataset / 'baselines.json', data_manifest['sha256']['baselines.json'])
    calendar = [block_counts(grid(start, end - timedelta(days=30)), start)
                for _, start, end in FOLDS]
    if all(sum(n >= 3 for n in blocks.values()) >= 6 for blocks in calendar):
        raise ValueError('Unsupported-fold evaluator cannot perform a sigmoid fit')
    out = TMP / 'phase05b-calibration-v1.1'
    out.mkdir(exist_ok=False)
    (out / 'access.json').write_bytes(canonical_bytes({
        'authorization': freeze['authorization'], 'freeze_sha256': args.freeze_sha256,
        'calibration': [START.isoformat(), END.isoformat()],
        'locked_status_fields': 'NOT_AUTHORIZED', 'operation': 'read calibration prefix only',
    }))
    records, fingerprint = prefix(dataset / 'observations.csv', END)
    _, earlier_fingerprint = prefix(TMP / 'phase05b-six-year-42017-v2/observations.csv', END)
    if fingerprint != earlier_fingerprint:
        raise ValueError('Calibration prefix differs from prior export')
    folds = []
    for (fit_end, start, end), blocks in zip(FOLDS, calendar):
        fit, fit_excluded = cohort(records, START, fit_end)
        assessment, assessment_excluded = cohort(records, start, end)
        folds.append({'fit_cutoff': fit_end.isoformat(), 'assessment_start': start.isoformat(),
                      'assessment_end': end.isoformat(), 'calendar_blocks': dict(blocks),
                      'fit': summary(fit, START), 'assessment': summary(assessment, start),
                      'fit_exclusions': fit_excluded, 'assessment_exclusions': assessment_excluded})
    all_rows, excluded = cohort(records, START, END)
    result = {
        'protocol_freeze_sha256': args.freeze_sha256, 'prefix_sha256': fingerprint,
        'primary': 'persistence_recovery', 'comparator': 'lr-c1_raw',
        'sigmoid': 'NOT_FITTED_INSUFFICIENT_TIME_BLOCKS', 'locked_test': 'NOT_RUN',
        'folds': folds, 'support': summary(all_rows, START),
        'exclusions': excluded, 'recovery': recovery_report(all_rows, baseline),
    }
    result_path = out / 'result.json'
    result_path.write_bytes(canonical_bytes(result))
    (out / 'seal.json').write_bytes(canonical_bytes({
        'result_sha256': digest(result_path), 'access_sha256': digest(out / 'access.json'),
        'freeze_sha256': args.freeze_sha256, 'comparator': 'lr-c1_raw', 'coefficients': None,
    }))
    print(result_path, digest(result_path))


if __name__ == '__main__':
    main()
