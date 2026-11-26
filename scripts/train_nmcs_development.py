"""Authorized development fitting only. Never consumes reserved outcome partitions."""
import argparse
from collections import Counter
import csv
from datetime import date
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from statistics import mean
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prediction.experiments import (canonical_bytes, verify_manifest, default_periods,
    EmpiricalBaselines, METHODS, SCHEMA as BASE_SCHEMA)
from prediction.ml_development import (SEED, SCHEMA, HORIZONS, CANDIDATES, SELECTION, NUMERIC,
    COLUMNS, CATEGORICAL_FEATURES, load_observations, development_section, make_batch, audit_batch,
    fit_candidate, predict, summarize, paired_brier_interval, score)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    path.write_bytes(canonical_bytes(value))


def interpret(pipeline, batch, algorithm):
    import numpy as np
    if algorithm == 'logistic':
        coefficients = pipeline.named_steps['classifier'].coef_[0]
        names = pipeline.named_steps['preprocess'].get_feature_names_out()
        top = sorted(zip(names,coefficients),key=lambda v:abs(v[1]),reverse=True)[:15]
        return {'kind':'standardized_numeric_and_one_hot_coefficients',
                'top':[{ 'feature':str(k),'coefficient':float(v)} for k,v in top],
                'limitation':'Conditional associations with correlated predictors, not causes.'}
    # Bounded grouped permutation on DEVELOPMENT only, never calibration/test.
    rng = np.random.default_rng(SEED)
    indices = rng.choice(len(batch.labels),size=min(1600,len(batch.labels)),replace=False)
    original = batch.frame.iloc[indices].reset_index(drop=True)
    y = batch.labels[indices]
    base = score(y,predict(pipeline,original))['brier']
    groups = {'horizon':['horizon_days'], 'current_status':['current_status'],
              'command':['command'], 'platform':['platform'],
              'state_age':['current_state_days_lower_bound'],
              'nmcs_history':[c for c in NUMERIC if ('nmcs' in c and not c.startswith('nmcs_x_'))
                               or c=='completed_nmcs_duration_mean']}
    result = {}
    for group,columns in groups.items():
        deltas = []
        for _ in range(3):
            changed = original.copy()
            order = rng.permutation(len(original))
            changed.loc[:,columns] = original.loc[:,columns].iloc[order].to_numpy()
            changed['log_horizon'] = np.log1p(changed['horizon_days'])
            flag = changed['current_status'].eq('NMCS').astype(float)
            changed['nmcs_x_horizon'] = flag * changed['horizon_days']
            changed['nmcs_x_log_horizon'] = flag * changed['log_horizon']
            deltas.append(score(y,predict(pipeline,changed))['brier']-base)
        result[group] = {'mean_brier_increase':float(np.mean(deltas)),
                         'repeat_deltas':[float(v) for v in deltas]}
    return {'kind':'grouped_development_permutation','rows':len(indices),'repeats':3,'groups':result,
            'limitation':'Descriptive; correlation/permutation shift and selection bias preclude causal interpretation.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment',default='phase05b-ml-development-v1')
    args = parser.parse_args()
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.experiment):
        parser.error('Workspace-local evidence identifier required')
    expected = ROOT/'.harness-test-tmp/phase05b-ml-env'
    if Path(sys.prefix).resolve() != expected.resolve():
        raise RuntimeError('Use the already qualified isolated scientific environment')
    runtime = json.loads((ROOT/'.harness-test-tmp/phase05b-runtime-qualification-v1/final-result.json').read_text())
    if runtime['status']!='PASS' or sys.version_info[:3]!=(3,13,7):
        raise RuntimeError('Qualified runtime is required')
    versions = {name:importlib.metadata.version(name) for name in runtime['installed_versions']}
    if versions != runtime['installed_versions']:
        raise RuntimeError('Approved scientific package versions changed')
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[name] = '1'
    import numpy as np
    import pandas as pd
    import joblib
    source = ROOT/'.harness-test-tmp/phase05b-six-year-42017-v3'
    if sha(source/'manifest.json')!='ff827565c2809bee36681456630155f99aa8ecad42dc5dcd78c4ad1c9bda089b':
        raise RuntimeError('Approved dataset manifest changed')
    manifest = json.loads((source/'manifest.json').read_text())
    verify_manifest(source,manifest)  # Hashes only; no decoding of reserved outcomes.
    baseline_raw = json.loads((source/'baselines.json').read_text())
    if (baseline_raw['feature_schema']!=BASE_SCHEMA or baseline_raw['target']!='NMCS_occupancy_at_T_plus_H'
            or baseline_raw['source']!='fictional_synthetic'):
        raise RuntimeError('Unexpected empirical artifact contract')
    baseline = EmpiricalBaselines(date.fromisoformat(baseline_raw['training_start']),
        date.fromisoformat(baseline_raw['training_outcome_cutoff']), tuple(baseline_raw['state_counts']),
        tuple(tuple(r) for r in baseline_raw['transition_counts']),
        tuple(tuple(tuple(c) for c in rows) for rows in baseline_raw['horizon_counts']),
        tuple(tuple(r) for r in baseline_raw['transition_probabilities']))
    train, validation, _, _ = default_periods()
    if (baseline.training_start,baseline.training_end)!=(train.start,train.end):
        raise RuntimeError('Empirical baseline was not frozen at the training outcome cutoff')
    old_development = development_section(source/'development_report.json')
    strongest = min(METHODS,key=lambda method:mean(old_development['horizons'][str(h)][method]['brier'] for h in HORIZONS))
    destination = ROOT/'.harness-test-tmp'/args.experiment
    destination.mkdir(exist_ok=False)
    revision = subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),
                                       'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    source_files = ('prediction/nmcs.py','prediction/experiments.py','prediction/ml_development.py',
                    'scripts/train_nmcs_development.py')
    plan = {'experiment':args.experiment,'schema':SCHEMA,'base_schema':BASE_SCHEMA,'seed':SEED,
            'source_revision':revision,'source_sha256':{p:sha(ROOT/p) for p in source_files},
            'python':sys.version,'platform':sys.platform,
            'dataset_manifest_sha256':sha(source/'manifest.json'), 'runtime':versions,
            'periods':{'train':[train.start.isoformat(),train.end.isoformat()],
                       'validation':[validation.start.isoformat(),validation.end.isoformat()]},
            'reserved_partitions':'NOT_CONSUMED_OR_EVALUATED',
            'train_reference_stride_days':14,'training_offsets':'one seed-fixed offset per 10-day bin, all 1..180 supported',
            'validation_reference_stride_days':7,'validation_purge_horizon':180,
            'horizons':HORIZONS,'candidates':CANDIDATES,'selection':SELECTION,
            'frozen_strongest_baseline':strongest,'numeric_features':NUMERIC,
            'categorical_features':CATEGORICAL_FEATURES,'threads':1,
            'imbalance_policy':'No resampling/class weighting; preserve observed occupancy probabilities; proper scoring and subgroup diagnostics.'}
    write(destination/'pre_fit_plan.json',plan)
    started = perf_counter()
    history = load_observations(source/'observations.csv',validation.end)
    print('Data verified; reserved statuses excluded before Observation construction',flush=True)
    training = make_batch(history,'train')
    development = make_batch(history,'validation')
    audit_batch(training);audit_batch(development)
    prepared_seconds = perf_counter()-started
    n_per_h = Counter(r['horizon'] for r in development.metadata)
    if set(n_per_h)!={*HORIZONS} or set(n_per_h.values())!={old_development['common_examples_per_horizon']}:
        raise RuntimeError('Validation cohort differs from the published empirical comparison')
    baseline_predictions = {m:np.asarray([baseline.predict(r['current_status'],r['horizon'],m)
                            for r in development.metadata]) for m in METHODS}
    reports = {m:summarize(development,p) for m,p in baseline_predictions.items()}
    for method in METHODS:
        for horizon in HORIZONS:
            if not np.isclose(reports[method][horizon]['brier'],
                              old_development['horizons'][str(horizon)][method]['brier'],atol=1e-12,rtol=0):
                raise RuntimeError('Reused baseline predictions/cohort changed')
    print(f'Prepared {len(training.labels)} training and {len(development.labels)} development examples',flush=True)
    summaries, predictions, artifact_paths = {}, {}, []
    for config in CANDIDATES:
        t = perf_counter()
        model, detail = fit_candidate(training,config)
        values = predict(model,development.frame)
        offset_checks = {}
        for is_nmcs in (False,True):
            first = next(i for i,r in enumerate(development.metadata) if (r['current_status']=='NMCS')==is_nmcs)
            grid = pd.concat([development.frame.iloc[[first]]]*180,ignore_index=True)
            grid['horizon_days'] = np.arange(1,181,dtype=float)
            grid['log_horizon'] = np.log1p(grid['horizon_days'])
            flag = grid['current_status'].eq('NMCS').astype(float)
            grid['nmcs_x_horizon'] = flag*grid['horizon_days']
            grid['nmcs_x_log_horizon'] = flag*grid['log_horizon']
            checked = predict(model,grid)
            offset_checks[str(is_nmcs)] = {'offsets':180,'probability_min':float(checked.min()),
                                           'probability_max':float(checked.max())}
        report = summarize(development,values)
        for h in HORIZONS:
            indices = report[h]['paired_indices']
            report[h]['paired_vs_strongest'] = paired_brier_interval(
                [development.metadata[i] for i in indices], development.labels[indices],
                values[indices],baseline_predictions[strongest][indices],h)
        detail.update(config=config,fit_and_score_seconds=perf_counter()-t,all_offset_checks=offset_checks,
                      mean_brier=mean(report[h]['brier'] for h in HORIZONS),
                      mean_log_loss=mean(report[h]['log_loss'] for h in HORIZONS),
                      already_nmcs_mean_brier=mean(report[h]['current_nmcs_groups']['NMCS']['brier'] for h in HORIZONS),
                      not_nmcs_mean_brier=mean(report[h]['current_nmcs_groups']['other']['brier'] for h in HORIZONS),
                      interpretability=interpret(model,development,config['algorithm']))
        artifact = destination/(config['id']+'.joblib')
        joblib.dump(model,artifact,compress=3)
        artifact_paths.append(artifact)
        summaries[config['id']] = {'fit':detail,'horizons':report}
        predictions[config['id']] = values
        print(config['id'], 'mean Brier',detail['mean_brier'],'converged',detail['converged'],flush=True)
    valid = [k for k,v in summaries.items() if v['fit']['converged']]
    if not valid:
        raise RuntimeError('No converged candidate; no configuration selected')
    ordered = sorted(valid,key=lambda k:(summaries[k]['fit']['mean_brier'],summaries[k]['fit']['mean_log_loss'],k))
    best = ordered[0]
    best_report = summaries[best]
    base_mean = mean(reports[strongest][h]['brier'] for h in HORIZONS)
    improvement = 1-best_report['fit']['mean_brier']/base_mean
    worst = max(best_report['horizons'][h]['brier']/reports[strongest][h]['brier']-1 for h in HORIZONS)
    reliability = best_report['fit']['mean_log_loss'] <= mean(reports[strongest][h]['log_loss'] for h in HORIZONS)
    practical = improvement>=SELECTION['practical_relative_brier_gain'] and worst<=SELECTION['maximum_per_horizon_relative_brier_degradation'] and reliability
    result = {'experiment':args.experiment,'schema':SCHEMA,'plan_sha256':sha(destination/'pre_fit_plan.json'),
        'preparation_seconds':prepared_seconds,'total_seconds':perf_counter()-started,
        'data_read_through':validation.end.isoformat(),'reserved_outcomes':'NOT_READ',
        'training':{'n':len(training.labels),'positive':int(training.labels.sum()),
                    'reference_start':min(r['reference_date'] for r in training.metadata),
                    'reference_end':max(r['reference_date'] for r in training.metadata),
                    'target_end':max(r['target_date'] for r in training.metadata),
                    'horizon_counts':dict(Counter(r['horizon'] for r in training.metadata))},
        'development':{'n':len(development.labels),'examples_per_horizon':dict(n_per_h),
                       'reference_start':min(r['reference_date'] for r in development.metadata),
                       'reference_end':max(r['reference_date'] for r in development.metadata),
                       'target_end':max(r['target_date'] for r in development.metadata)},
        'baselines':reports,'candidates':summaries,'strongest_baseline':strongest,
        'provisional_best_ml':best,'frozen_configuration':best_report['fit']['config'],
        'mean_relative_brier_gain':improvement,'worst_horizon_relative_brier_degradation':worst,
        'log_loss_reliability_pass':reliability,'predeclared_practical_criteria_pass':practical,
        'recommendation':('CALIBRATION_EXPERIMENT_ONLY_FOR_FROZEN_CANDIDATE' if practical
                          else 'RETAIN_EMPIRICAL_BASELINE_NO_ML_CHAMPION'),
        'uncertainty':'Development only; long horizons have <5 time clusters. No confirmatory superiority.',
        'calibration':'NOT_RUN','locked_test':'NOT_RUN','phase05c':'NO_GO','model_promotion':'NONE'}
    write(destination/'development_results.json',result)
    with (destination/'development_predictions.csv').open('w',encoding='utf-8',newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['tail','reference_date','horizon','target_date','label',*METHODS,*predictions])
        for i,row in enumerate(development.metadata):
            writer.writerow([row['tail'],row['reference_date'],row['horizon'],row['target_date'],int(development.labels[i]),
                             *(float(baseline_predictions[m][i]) for m in METHODS),
                             *(float(predictions[m][i]) for m in predictions)])
    write(destination/'frozen_candidate.json',{'model_id':best,'configuration':best_report['fit']['config'],
        'schema':SCHEMA,'calibration':'NOT_RUN','promotion':'NONE','provisional_only':True})
    artifacts = [destination/'pre_fit_plan.json',destination/'development_results.json',
                 destination/'development_predictions.csv',destination/'frozen_candidate.json',*artifact_paths]
    write(destination/'manifest.json',{'format':'fis4-nmcs-development-v1','source':'fictional_synthetic',
        'source_revision':revision,'working_source_sha256':plan['source_sha256'],'schema':SCHEMA,
        'dataset_manifest_sha256':plan['dataset_manifest_sha256'],'runtime':versions,
        'approved_outcome_cutoff':validation.end.isoformat(),'training_outcome_cutoff':train.end.isoformat(),
        'reserved_outcomes_consumed':False,'pre_fit_plan_sha256':sha(destination/'pre_fit_plan.json'),
        'sha256':{p.name:sha(p) for p in artifacts}})
    print('Development complete:',best,result['recommendation'],'calibration/test NOT_RUN',flush=True)


if __name__=='__main__':
    main()
