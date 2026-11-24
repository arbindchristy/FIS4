"""Offline, dependency-independent empirical baselines and temporal preparation.

No ML estimator, network, artifact deserialization or application integration.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib
import json
import math
import random
from statistics import mean

from prediction.nmcs import History, features_at, reconstruct, target_at


STATES = ('FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT')
METHODS = ('historical_occupancy', 'persistence_recovery', 'transition_rule')
SCHEMA = 'nmcs-occupancy-features-v1'
NUMERIC_FEATURES = ('horizon_days', 'days_since_last_nmcs', 'current_state_days_lower_bound',
                    'completed_nmcs_duration_mean', 'nmcs_recurrence_interval_mean',
                    'hrs_to_insp', 'hrs_to_phase') + tuple(
    f'{name}_{w}' for w in (30, 90, 180, 365) for name in ('nmcs_days', 'nmcs_known_starts'))
CATEGORICAL_FEATURES = ('current_status', 'command', 'platform')


@dataclass(frozen=True)
class Period:
    name: str
    start: date
    end: date

    def __post_init__(self):
        if type(self.start) is not date or type(self.end) is not date or self.start > self.end:
            raise ValueError('Invalid calendar period')


def default_periods():
    return (Period('train', date(2020, 11, 21), date(2023, 11, 20)),
            Period('validation', date(2023, 11, 21), date(2024, 11, 20)),
            Period('calibration', date(2024, 11, 21), date(2025, 11, 20)),
            Period('locked_test', date(2025, 11, 21), date(2026, 11, 20)))


def validate_periods(periods):
    if tuple(p.name for p in periods) != ('train', 'validation', 'calibration', 'locked_test'):
        raise ValueError('Four ordered scientific partitions required')
    for left, right in zip(periods, periods[1:]):
        if left.end >= right.start:
            raise ValueError('Partitions must not overlap')


def references(history: History, period: Period, horizon: int, *, stride_days=1):
    if type(horizon) is not int or not 1 <= horizon <= 180:
        raise ValueError('Offset must be an integer in 1..180')
    if type(stride_days) is not int or stride_days < 1:
        raise ValueError('Positive integer reference stride required')
    day = period.start
    while day + timedelta(days=horizon) <= min(period.end, history.cutoff.date()):
        for tail in sorted(history.by_tail):
            label = target_at(history, tail, day, horizon)
            if label.value is not None:
                yield tail, day, label
        day += timedelta(days=stride_days)


def prepare_example(history: History, period: Period, tail: str, day: date, horizon: int):
    if not period.start <= day <= period.end:
        raise ValueError('Reference outside authorized period')
    label = target_at(history, tail, day, horizon)
    if label.target_date > period.end or label.value is None:
        raise ValueError('Outcome unavailable within authorized partition')
    raw = features_at(history, tail, day)
    flat = {name: raw[name] for name in NUMERIC_FEATURES[1:7]}
    flat['horizon_days'] = horizon
    for w, values in raw['windows'].items():
        for name in ('nmcs_days', 'nmcs_known_starts'):
            flat[f'{name}_{w}'] = values[name]
    return {'schema': SCHEMA, 'numeric': tuple(flat[name] for name in NUMERIC_FEATURES),
            'categorical': tuple(raw[name] for name in CATEGORICAL_FEATURES),
            'target': label.value, 'target_date': label.target_date.isoformat(),
            'reference_date': day.isoformat(), 'tail': tail}


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


@dataclass(frozen=True)
class EmpiricalBaselines:
    training_start: date
    training_end: date
    state_counts: tuple[int, ...]
    transition_counts: tuple[tuple[int, ...], ...]
    horizon_counts: tuple[tuple[tuple[int, int], ...], ...]
    transition_probabilities: tuple[tuple[float, ...], ...]

    @property
    def occupancy(self):
        return self.state_counts[3] / sum(self.state_counts)

    def predict(self, state: str, horizon: int, method: str):
        if state not in STATES or method not in METHODS:
            raise ValueError('Unknown state or baseline')
        if type(horizon) is not int or not 1 <= horizon <= 180:
            raise ValueError('Offset must be an integer in 1..180')
        i = STATES.index(state)
        if method == 'historical_occupancy':
            return self.occupancy
        if method == 'transition_rule':
            return self.transition_probabilities[horizon - 1][i]
        positives, total = self.horizon_counts[horizon - 1][i]
        return positives / total if total else self.occupancy

    def forecast(self, history: History, tail: str, day: date, horizon: int, method: str):
        if type(day) is not date or day <= self.training_end:
            raise ValueError('Replay requires reference after frozen training cutoff')
        row = history.reference_at(tail, day)
        if row is None:
            raise ValueError('Reference state unavailable')
        probability = self.predict(row.status, horizon, method)
        i = STATES.index(row.status)
        positives, cohort = self.horizon_counts[horizon - 1][i]
        return {'method': method, 'horizon_days': horizon,
                'target_date': (day + timedelta(days=horizon)).isoformat(),
                'probability': probability, 'current_status': row.status,
                'explanation': {'training_start': self.training_start.isoformat(),
                    'training_outcome_cutoff': self.training_end.isoformat(),
                    'training_nmcs_days': self.state_counts[3],
                    'training_usable_days': sum(self.state_counts),
                    'same_state_same_horizon_positive': positives,
                    'same_state_same_horizon_support': cohort,
                    'same_state_transition_counts': self.transition_counts[i],
                    'conditional_fallback': method == 'persistence_recovery' and cohort == 0,
                    'limitations': 'Empirical training associations; not causes or calibrated ML. '
                                   'Transition rule assumes time-homogeneous first-order states.'}}

    def artifact(self):
        return {'format': 'fis4-empirical-baselines-v1', 'feature_schema': SCHEMA,
                'target': 'NMCS_occupancy_at_T_plus_H', 'source': 'fictional_synthetic',
                'training_start': self.training_start.isoformat(),
                'training_outcome_cutoff': self.training_end.isoformat(),
                'states': STATES, 'state_counts': self.state_counts,
                'transition_counts': self.transition_counts, 'horizon_counts': self.horizon_counts,
                'transition_probabilities': self.transition_probabilities,
                'hyperparameters': {'horizons': [1, 180], 'smoothing': 'none',
                                    'empty_cohort': 'training occupancy',
                                    'transition_assumption': 'first-order time homogeneous'},
                'ml_candidate_status': 'BLOCKED_dependencies_unavailable'}


def fit_baselines(history: History, training: Period):
    if training.name != 'train' or training.end > history.cutoff.date():
        raise ValueError('Explicit authorized training cutoff required')
    # A fresh cutoff view prevents future rows/outcomes/endpoint extension in fitting.
    visible = reconstruct(history.observations,
                          cutoff=datetime.combine(training.end, time.max),
                          validated_reconstruction=history.validated_reconstruction)
    rows_by_tail = {tail: tuple(r for r in rows if r.date >= training.start)
                    for tail, rows in visible.by_tail.items()}
    state_counts = [0] * 6
    transitions = [[0] * 6 for _ in STATES]
    for rows in rows_by_tail.values():
        for row in rows:
            if row.usable:
                state_counts[STATES.index(row.status)] += 1
        for before, after in zip(rows, rows[1:]):
            if before.usable and after.usable:
                transitions[STATES.index(before.status)][STATES.index(after.status)] += 1
    if not sum(state_counts):
        raise ValueError('No usable training history')
    masks = {tail: tuple(visible.reference_at(tail, r.date) is not None for r in rows)
             for tail, rows in rows_by_tail.items()}
    cohorts = []
    for horizon in range(1, 181):
        counts = [[0, 0] for _ in STATES]
        for tail, rows in rows_by_tail.items():
            for before, after, valid in zip(rows, rows[horizon:], masks[tail]):
                if valid and after.usable:
                    group = counts[STATES.index(before.status)]
                    group[0] += after.status == 'NMCS'
                    group[1] += 1
        cohorts.append(tuple(tuple(c) for c in counts))
    distribution = [c / sum(state_counts) for c in state_counts]
    matrix = [[c / sum(row) for c in row] if sum(row) else distribution[:] for row in transitions]
    probabilities = []
    vector = [float(s == 'NMCS') for s in STATES]
    for _ in range(180):
        vector = [sum(matrix[i][j] * vector[j] for j in range(6)) for i in range(6)]
        probabilities.append(tuple(min(1., max(0., p)) for p in vector))
    return EmpiricalBaselines(training.start, training.end, tuple(state_counts),
                              tuple(tuple(r) for r in transitions), tuple(cohorts), tuple(probabilities))


def metrics(pairs):
    """Brier, rank AUC, tie-aware AP/lift and fixed-bin calibration diagnostics."""
    pairs = list(pairs)
    if not pairs or any(type(y) is not int or y not in (0, 1) or not math.isfinite(p)
                        or not 0 <= p <= 1 for y, p in pairs):
        raise ValueError('Finite probabilities and binary outcomes required')
    n = len(pairs)
    positives = sum(y for y, _ in pairs)
    # Converged Markov states can differ by machine epsilon; do not rank noise.
    ranked = [(y, round(p, 12)) for y, p in pairs]
    ordered = sorted(ranked, key=lambda r: r[1], reverse=True)
    tp = fp = area = ap = 0.
    top_count = max(1., n * .1)
    top_positive = 0.
    consumed = 0
    for score in sorted({p for _, p in ranked}, reverse=True):
        group = [y for y, p in ordered[consumed:] if p == score]
        gp = sum(group)
        gn = len(group) - gp
        # ROC trapezoids and AP over tied-score groups, not arbitrary tail order.
        area += gn * (tp + gp / 2)
        tp += gp
        fp += gn
        if positives:
            ap += gp / positives * tp / (tp + fp)
        top_positive += gp * min(1., max(0., top_count - consumed) / len(group))
        consumed += len(group)
    calibration = []
    for b in range(10):
        group = [(y, p) for y, p in pairs if min(9, int(p * 10)) == b]
        calibration.append({'bin': b, 'count': len(group),
                            'predicted': mean(p for _, p in group) if group else None,
                            'observed': mean(y for y, _ in group) if group else None})
    prevalence = positives / n
    return {'n': n, 'positive': positives, 'prevalence': prevalence, 'ranking_probability_decimals': 12,
            'brier': mean((p - y)**2 for y, p in pairs),
            'roc_auc': area / (positives * (n - positives)) if 0 < positives < n else None,
            'pr_auc_average_precision': ap if 0 < positives < n else None,
            'top_decile_lift': top_positive / top_count / prevalence if prevalence else None,
            'ece_10_bins': sum(g['count'] / n * abs(g['predicted'] - g['observed'])
                               for g in calibration if g['count']),
            'calibration': calibration}


def clustered_brier_interval(rows, *, seed=42017, replicates=200):
    """Exploratory two-way (tail and 28-day reference block) pigeonhole bootstrap."""
    if not rows:
        return None
    tails = sorted({r['tail'] for r in rows})
    blocks = sorted({date.fromisoformat(r['reference_date']).toordinal() // 28 for r in rows})
    if len(tails) < 2 or len(blocks) < 2:
        return None
    rng = random.Random(seed)
    estimates = []
    cells = {}
    for r in rows:
        key = (r['tail'], date.fromisoformat(r['reference_date']).toordinal() // 28)
        loss, count = cells.get(key, (0., 0))
        cells[key] = (loss + (r['probability'] - r['outcome'])**2, count + 1)
    for _ in range(replicates):
        tw = dict.fromkeys(tails, 0)
        bw = dict.fromkeys(blocks, 0)
        for t in rng.choices(tails, k=len(tails)):
            tw[t] += 1
        for b in rng.choices(blocks, k=len(blocks)):
            bw[b] += 1
        loss = total = 0.
        for (tail, block), (value, n) in cells.items():
            weight = tw[tail] * bw[block]
            loss += weight * value
            total += weight * n
        if total:
            estimates.append(loss / total)
    if not estimates:
        return None
    estimates.sort()
    return {'lower': estimates[int(.025 * (len(estimates) - 1))],
            'upper': estimates[int(.975 * (len(estimates) - 1))],
            'replicates': len(estimates), 'tail_clusters': len(tails), 'time_clusters': len(blocks),
            'limitation': 'Exploratory marginal Brier interval, not paired improvement evidence; '
                          '28-day blocks do not remove all 180-day outcome dependence.'}


def verify_manifest(directory, manifest):
    """Verify own JSON/CSV evidence hashes; never load executable estimators."""
    if manifest.get('format') != 'fis4-modeling-preparation-v1' or manifest.get('feature_schema') != SCHEMA:
        raise ValueError('Unknown artifact schema')
    if manifest.get('source') != 'fictional_synthetic' or not manifest.get('source_revision'):
        raise ValueError('Missing fictional provenance')
    allowed = {'observations.csv', 'baselines.json', 'development_report.json'}
    if set(manifest.get('sha256', {})) != allowed:
        raise ValueError('Unexpected artifact inventory')
    for name, digest in manifest['sha256'].items():
        path = directory / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Artifact integrity check failed')
    return True
