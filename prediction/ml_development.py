"""Bounded offline development only; sklearn imports are isolated/lazy.

No calibration, locked-test scoring, production API or untrusted model loading.
"""
import csv
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib
import json
import math
import random
from statistics import mean

from prediction.nmcs import Observation, reconstruct, features_at, target_at
from prediction.experiments import (NUMERIC_FEATURES, CATEGORICAL_FEATURES, STATES,
                                    default_periods, metrics)


SEED = 42017
SCHEMA = 'nmcs-horizon-development-v1'
HORIZONS = (7, 14, 30, 45, 60, 90, 120, 123, 150, 180)
ADDITIONS = ('history_days', 'usable_history_days', 'history_complete',
             'current_state_left_censored', 'nmcs_left_censored_fragments')
DERIVED = ('log_horizon', 'nmcs_x_horizon', 'nmcs_x_log_horizon')
NUMERIC = NUMERIC_FEATURES + ADDITIONS + DERIVED
COLUMNS = NUMERIC + CATEGORICAL_FEATURES
CANDIDATES = (
    {'id': 'lr-c01', 'algorithm': 'logistic', 'C': .1, 'l1_ratio': 0.,
     'solver': 'lbfgs', 'tol': 1e-6, 'max_iter': 1000, 'class_weight': None, 'random_state': SEED},
    {'id': 'lr-c1', 'algorithm': 'logistic', 'C': 1., 'l1_ratio': 0.,
     'solver': 'lbfgs', 'tol': 1e-6, 'max_iter': 1000, 'class_weight': None, 'random_state': SEED},
    {'id': 'hgb-15', 'algorithm': 'hist_gradient_boosting', 'loss': 'log_loss',
     'learning_rate': .05, 'max_iter': 150, 'max_leaf_nodes': 15, 'max_depth': 4,
     'min_samples_leaf': 200, 'l2_regularization': 10., 'max_bins': 127,
     'early_stopping': False, 'class_weight': None, 'random_state': SEED},
    {'id': 'hgb-7', 'algorithm': 'hist_gradient_boosting', 'loss': 'log_loss',
     'learning_rate': .05, 'max_iter': 150, 'max_leaf_nodes': 7, 'max_depth': 3,
     'min_samples_leaf': 200, 'l2_regularization': 10., 'max_bins': 127,
     'early_stopping': False, 'class_weight': None, 'random_state': SEED},
)
SELECTION = {
    'primary': 'equal-horizon mean development Brier; converged candidates only',
    'practical_relative_brier_gain': .02,
    'maximum_per_horizon_relative_brier_degradation': .05,
    'reliability': 'mean log loss no worse than frozen strongest empirical baseline',
    'uncertainty': 'paired tail/time bootstrap; <5 time clusters unsupported; no confirmatory claim',
    'tie_break': 'log loss then simpler candidate ID; no search beyond four fixed configurations',
    'promotion': 'NONE; calibration and locked test reserved',
}


@dataclass
class Batch:
    role: str
    frame: object
    labels: object
    metadata: tuple


def load_observations(path, cutoff):
    """Filter timestamp before status/context access; never construct reserved rows."""
    if type(cutoff) is not date or cutoff > default_periods()[1].end:
        raise ValueError('Development cannot read beyond the validation outcome cutoff')
    records = []
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['date', 'tail', 'status', 'command', 'platform']:
            raise ValueError('Approved fictional event projection required')
        for row in reader:
            timestamp = datetime.fromisoformat(row['date'])
            if timestamp.date() > cutoff:
                continue
            records.append(Observation(timestamp, row['tail'], row['status'], row['command'], row['platform']))
    return reconstruct(records, cutoff=datetime.combine(cutoff, time.max), validated_reconstruction=True)


def development_section(path):
    """Decode only the old validation baseline section, never full-period statistics."""
    raw = path.read_bytes()
    marker = b'"development_replay":'
    start = raw.index(marker) + len(marker)
    section, _ = json.JSONDecoder().raw_decode(raw[start:].decode('utf-8').lstrip())
    if section['kind'] != 'model_development_validation_only':
        raise ValueError('Expected published development-only evidence')
    return section


def sampled_horizons(tail, day, max_horizon, seed=SEED):
    if type(max_horizon) is not int or not 1 <= max_horizon <= 180:
        raise ValueError('Bounded available horizon required')
    digest = hashlib.sha256(f'{seed}:{tail}:{day.isoformat()}'.encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], 'big'))
    return tuple(rng.randint(low, min(low + 9, max_horizon)) for low in range(1, max_horizon + 1, 10))


def feature_row(raw, horizon):
    if type(horizon) is not int or not 1 <= horizon <= 180:
        raise ValueError('Forecast offset must be in 1..180')
    row = {name: raw[name] for name in NUMERIC_FEATURES[1:7]}
    row['horizon_days'] = horizon
    for w, values in raw['windows'].items():
        for name in ('nmcs_days', 'nmcs_known_starts'):
            row[f'{name}_{w}'] = values[name]
    row.update({name: raw[name] for name in ADDITIONS + CATEGORICAL_FEATURES})
    row['log_horizon'] = math.log1p(horizon)
    row['nmcs_x_horizon'] = horizon * int(raw['current_status'] == 'NMCS')
    row['nmcs_x_log_horizon'] = row['log_horizon'] * int(raw['current_status'] == 'NMCS')
    return row


def make_batch(history, role, *, train_stride=14, validation_stride=7):
    import numpy as np
    import pandas as pd
    train, validation, _, _ = default_periods()
    if role not in ('train', 'validation'):
        raise ValueError('Calibration and locked-test preparation are not authorized')
    if any(type(s) is not int or s < 1 for s in (train_stride, validation_stride)):
        raise ValueError('Positive integer calendar strides required')
    period = train if role == 'train' else validation
    history = reconstruct(history.observations,
                          cutoff=min(history.cutoff, datetime.combine(period.end,time.max)),
                          validated_reconstruction=history.validated_reconstruction)
    rows, labels, metadata = [], [], []
    day = period.start
    maximum = 1 if role == 'train' else 180
    while day + timedelta(days=maximum) <= min(period.end, history.cutoff.date()):
        for tail in sorted(history.by_tail):
            if history.reference_at(tail, day) is None:
                continue
            offsets = (sampled_horizons(tail, day, min(180, (period.end-day).days))
                       if role == 'train' else HORIZONS)
            outcomes = [target_at(history, tail, day, h) for h in offsets]
            if role == 'validation' and any(o.value is None for o in outcomes):
                continue
            raw = features_at(history, tail, day)
            for h, outcome in zip(offsets, outcomes):
                if outcome.value is None:
                    continue
                if outcome.target_date > period.end:
                    raise ValueError('Target crossed the authorized outcome boundary')
                rows.append(feature_row(raw, h))
                labels.append(outcome.value)
                metadata.append({'tail': tail, 'reference_date': day.isoformat(), 'horizon': h,
                                 'target_date': outcome.target_date.isoformat(),
                                 'current_status': raw['current_status'], 'command': raw['command'],
                                 'platform': raw['platform']})
        day += timedelta(days=train_stride if role == 'train' else validation_stride)
    if not rows:
        raise ValueError('No eligible examples')
    frame = pd.DataFrame(rows, columns=COLUMNS)
    for column in NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors='raise').astype('float64')
    return Batch(role, frame, np.asarray(labels, dtype=np.int8), tuple(metadata))


def audit_batch(batch):
    import numpy as np
    if batch.role not in ('train', 'validation') or tuple(batch.frame.columns) != COLUMNS:
        raise ValueError('Unexpected role or feature schema')
    period = default_periods()[0 if batch.role == 'train' else 1]
    if len(batch.frame) != len(batch.labels) or len(batch.labels) != len(batch.metadata):
        raise ValueError('Feature/label/cohort alignment failed')
    if not np.isin(batch.labels, [0, 1]).all():
        raise ValueError('NMCS occupancy requires binary labels')
    for row in batch.metadata:
        ref, target = date.fromisoformat(row['reference_date']), date.fromisoformat(row['target_date'])
        if (not period.start <= ref <= target <= period.end
                or not 1 <= row['horizon'] <= 180 or target-ref != timedelta(days=row['horizon'])):
            raise ValueError('Reference/target partition or horizon mismatch')
    if not np.array_equal(batch.frame['horizon_days'].to_numpy(), [r['horizon'] for r in batch.metadata]):
        raise ValueError('Horizon feature/target misalignment')
    return True


def fit_candidate(batch, configuration):
    import numpy as np
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits
    import warnings
    if batch.role != 'train':
        raise ValueError('Only the training partition may fit preprocessing or candidates')
    audit_batch(batch)
    if set(np.unique(batch.labels)) != {0, 1}:
        raise ValueError('Both training outcome classes required')
    # Drop unavailable inputs using TRAIN only; raw hours stay missing, not invented.
    active = [c for c in NUMERIC if batch.frame[c].notna().any()]
    dropped = [c for c in NUMERIC if c not in active]
    preprocessing = ColumnTransformer([
        ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True,
                                                       keep_empty_features=True)),
                              ('scale', StandardScaler())]), active),
        ('categorical', OneHotEncoder(handle_unknown='ignore', sparse_output=False,
                                     dtype=np.float64), list(CATEGORICAL_FEATURES))],
        remainder='drop', sparse_threshold=0.)
    params = {k: v for k, v in configuration.items() if k not in ('id', 'algorithm')}
    estimator = (LogisticRegression(**params) if configuration['algorithm'] == 'logistic'
                 else HistGradientBoostingClassifier(**params)
                 if configuration['algorithm'] == 'hist_gradient_boosting' else None)
    if estimator is None:
        raise ValueError('Unknown bounded candidate algorithm')
    pipeline = Pipeline([('preprocess', preprocessing), ('classifier', estimator)])
    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
        warnings.simplefilter('always')
        pipeline.fit(batch.frame, batch.labels)
    if list(estimator.classes_) != [0, 1]:
        raise ValueError('Unexpected NMCS positive-class ordering')
    return pipeline, {'dropped_all_missing_train_features': dropped,
                      'active_numeric_features': active,
                      'train_imputation_medians': {k:float(v) for k,v in zip(active,
                          preprocessing.named_transformers_['numeric'].named_steps['impute'].statistics_)},
                      'train_categories': {k:list(v) for k,v in zip(CATEGORICAL_FEATURES,
                          preprocessing.named_transformers_['categorical'].categories_)},
                      'transformed_features': list(preprocessing.get_feature_names_out()),
                      'warnings': [str(w.message) for w in caught],
                      'converged': not any(isinstance(w.message, ConvergenceWarning) for w in caught),
                      'iterations': np.asarray(estimator.n_iter_).tolist()}


def predict(pipeline, frame):
    import numpy as np
    from threadpoolctl import threadpool_limits
    if tuple(frame.columns) != COLUMNS:
        raise ValueError('Prediction schema mismatch')
    if (not frame['horizon_days'].between(1, 180).all()
            or not (frame['horizon_days'] % 1 == 0).all()):
        raise ValueError('Prediction offset outside 1..180')
    flag = frame['current_status'].eq('NMCS').astype(float)
    if (not np.allclose(frame['log_horizon'],np.log1p(frame['horizon_days']))
            or not np.allclose(frame['nmcs_x_horizon'],flag*frame['horizon_days'])
            or not np.allclose(frame['nmcs_x_log_horizon'],flag*frame['log_horizon'])):
        raise ValueError('Derived horizon features are inconsistent')
    with threadpool_limits(limits=1):
        values = pipeline.predict_proba(frame)[:, 1]
    if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
        raise ValueError('Invalid probability output')
    return values


def score(labels, probabilities):
    if not len(labels) or len(labels) != len(probabilities):
        raise ValueError('Aligned nonempty probability/outcome arrays required')
    result = metrics((int(y), float(p)) for y, p in zip(labels, probabilities))
    result['log_loss'] = mean(-math.log(max(1e-15, min(1-1e-15, float(p)))) if y
                              else -math.log(1-max(1e-15, min(1-1e-15, float(p))))
                              for y, p in zip(labels, probabilities))
    return result


def paired_brier_interval(metadata, labels, candidate, baseline, horizon, *, replicates=200):
    """Paired two-way cluster diagnostic; do not manufacture long-horizon intervals."""
    tails = sorted({r['tail'] for r in metadata})
    anchor = min(date.fromisoformat(r['reference_date']) for r in metadata).toordinal()
    width = max(28, horizon)
    cells = {}
    for row, y, p, q in zip(metadata, labels, candidate, baseline):
        block = (date.fromisoformat(row['reference_date']).toordinal()-anchor)//width
        key = (row['tail'], block)
        loss, n = cells.get(key, (0., 0))
        cells[key] = (loss + (float(p)-y)**2 - (float(q)-y)**2, n+1)
    blocks = sorted({b for _, b in cells})
    result = {'delta_brier': mean((float(p)-y)**2-(float(q)-y)**2 for y,p,q in zip(labels,candidate,baseline)),
              'block_days': width, 'tail_clusters': len(tails), 'time_clusters': len(blocks),
              'lower': None, 'upper': None,
              'status': 'insufficient_time_clusters' if len(blocks) < 5 or len(tails) < 2 else 'exploratory'}
    if result['status'] != 'exploratory':
        return result
    rng = random.Random(SEED)
    values = []
    for _ in range(replicates):
        tw, bw = dict.fromkeys(tails,0), dict.fromkeys(blocks,0)
        for t in rng.choices(tails,k=len(tails)): tw[t] += 1
        for b in rng.choices(blocks,k=len(blocks)): bw[b] += 1
        total = loss = 0.
        for (tail,block),(delta,n) in cells.items():
            w = tw[tail]*bw[block]
            total += w*n
            loss += w*delta
        if total: values.append(loss/total)
    values.sort()
    result.update(lower=values[int(.025*(len(values)-1))], upper=values[int(.975*(len(values)-1))],
                  replicates=len(values), limitation='Nominal post-selection development diagnostic; not independent confirmation.')
    return result


def summarize(batch, probabilities):
    import numpy as np
    output = {}
    for horizon in HORIZONS:
        indices = [i for i,r in enumerate(batch.metadata) if r['horizon']==horizon]
        y, p = batch.labels[indices], np.asarray(probabilities)[indices]
        meta = [batch.metadata[i] for i in indices]
        report = score(y,p)
        for field, values in [('current_nmcs', ('NMCS','other')),
                              ('command',sorted({r['command'] for r in meta})),
                              ('platform',sorted({r['platform'] for r in meta}))]:
            groups = {}
            for value in values:
                if field == 'current_nmcs':
                    selected = [j for j,r in enumerate(meta) if (r['current_status']=='NMCS') == (value=='NMCS')]
                else:
                    selected = [j for j,r in enumerate(meta) if r[field]==value]
                if not selected: continue
                group = score(y[selected],p[selected])
                if min(group['positive'],group['n']-group['positive']) < 10:
                    group.update(roc_auc=None,pr_auc_average_precision=None,top_decile_lift=None,
                                 ranking_status='insufficient_class_support')
                groups[value] = group
            report[field+'_groups'] = groups
        dates = {}
        for row, observed, probability in zip(meta,y,p):
            a = dates.setdefault(row['reference_date'],[0.,0,0])
            a[0] += float(probability);a[1] += int(observed);a[2] += 1
        report['fleet_counts'] = {'n_dates':len(dates), 'mean_expected':mean(v[0] for v in dates.values()),
                                 'mean_observed':mean(v[1] for v in dates.values()),
                                 'mean_absolute_error':mean(abs(v[0]-v[1]) for v in dates.values()),
                                 'cohort_sizes':sorted({v[2] for v in dates.values()})}
        report['paired_indices'] = indices
        output[horizon] = report
    return output
