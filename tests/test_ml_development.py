"""Fictional cutoff/cohort tests plus isolated-environment-only estimator tests."""
import copy
import csv
from datetime import date,datetime,timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from prediction.nmcs import Observation,reconstruct,features_at
from prediction.experiments import default_periods
from prediction.ml_development import (load_observations,development_section,sampled_horizons,
    feature_row,COLUMNS,CANDIDATES,SELECTION,make_batch,audit_batch,fit_candidate,predict,score,
    paired_brier_interval,Batch,HORIZONS)

START=default_periods()[0].start
STATES=('FMC','NMCS','NMCS','NMCM','FMC','PMCM','PMCS','DEPOT')


def observations():
    return [Observation(datetime.combine(START+timedelta(days=i),datetime.min.time()),
                        '000001',STATES[i%len(STATES)],'FICTIONAL_A','UH-60L') for i in range(65)]


def history(extra=()):
    rows=observations()+list(extra)
    return reconstruct(rows,cutoff=max(r.timestamp for r in rows),validated_reconstruction=True)


class DevelopmentBoundaryTests(unittest.TestCase):
    def test_reserved_outcomes_filtered_before_validation(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'events.csv'
            with path.open('w',newline='',encoding='utf-8') as f:
                writer=csv.writer(f);writer.writerow(['date','tail','status','command','platform'])
                writer.writerow(['2020-11-21T00:00:00','000001','FMC','FICTIONAL_A','UH-60L'])
                writer.writerow(['2025-01-01T00:00:00','','DO_NOT_CONSUME','',''])
            h=load_observations(path,default_periods()[1].end)
            self.assertEqual(len(h.observations),1)
            with self.assertRaises(ValueError):load_observations(path,date(2025,1,1))

    def test_decode_only_development_section(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'report.json'
            # Invalid JSON after the allowed object proves it is never decoded.
            path.write_text('{"development_replay":{"kind":"model_development_validation_only","n":3}, UNREAD_RESERVED',encoding='utf-8')
            self.assertEqual(development_section(path)['n'],3)

    def test_sampling_is_deterministic_and_supports_all_offsets(self):
        all_h=set()
        for i in range(100):
            day=START+timedelta(days=i)
            a=sampled_horizons('000001',day,180)
            self.assertEqual(a,sampled_horizons('000001',day,180))
            self.assertEqual(len(a),18)
            all_h.update(a)
        self.assertEqual(all_h,set(range(1,181)))
        self.assertEqual(sampled_horizons('000001',START,1),(1,))

    def test_exact_horizon_features_have_no_tail_or_target(self):
        raw=features_at(history(),'000001',START+timedelta(days=40))
        for h in range(1,181):
            row=feature_row(raw,h)
            self.assertEqual(set(row),set(COLUMNS))
            self.assertEqual(row['horizon_days'],h)
            self.assertNotIn('tail',row);self.assertNotIn('target',row)
            self.assertIsNone(row['hrs_to_insp']);self.assertIsNone(row['hrs_to_phase'])
        with self.assertRaises(ValueError):feature_row(raw,True)

    def test_training_policies_are_frozen_and_bounded(self):
        self.assertEqual(len(CANDIDATES),4)
        self.assertTrue(all(c['class_weight'] is None for c in CANDIDATES))
        self.assertTrue(all(c.get('early_stopping') is False for c in CANDIDATES if c['algorithm']=='hist_gradient_boosting'))
        self.assertEqual(SELECTION['promotion'],'NONE; calibration and locked test reserved')

    def test_probability_metrics_and_missing_long_horizon_uncertainty(self):
        self.assertAlmostEqual(score([0,1],[.2,.8])['log_loss'],.2231435513142097)
        with self.assertRaises(ValueError):score([0,1],[.2])
        metadata=[{'tail':t,'reference_date':(START+timedelta(days=d)).isoformat()}
                  for t in ('000001','000002') for d in (0,7,14,21)]
        ci=paired_brier_interval(metadata,[0,1]*4,[.2,.8]*4,[.3,.7]*4,180)
        self.assertEqual(ci['status'],'insufficient_time_clusters')
        self.assertIsNone(ci['upper'])


@unittest.skipUnless(importlib.util.find_spec('sklearn'), 'Requires qualified isolated scientific environment')
class IsolatedEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=make_batch(history(),'train')

    def test_training_cutoff_cannot_be_extended_by_future_data(self):
        import numpy as np
        future=Observation(datetime(2024,1,1),'000001','NMCS','FICTIONAL_A','UH-60L')
        actual=make_batch(history([future]),'train')
        self.assertTrue(self.batch.frame.equals(actual.frame))
        self.assertTrue(np.array_equal(self.batch.labels,actual.labels))
        self.assertEqual(self.batch.metadata,actual.metadata)

    def test_batch_boundaries_and_label_offset_audit(self):
        self.assertTrue(audit_batch(self.batch))
        bad=copy.deepcopy(self.batch)
        bad.metadata=tuple([{**bad.metadata[0],'target_date':'2024-01-01'},*bad.metadata[1:]])
        with self.assertRaises(ValueError):audit_batch(bad)
        with self.assertRaises(ValueError):make_batch(history(),'calibration')
        with self.assertRaises(ValueError):make_batch(history(),'locked_test')

    def test_nmcm_target_is_negative_and_current_nmcs_included(self):
        seen_current=False
        for y,row in zip(self.batch.labels,self.batch.metadata):
            offset=(date.fromisoformat(row['target_date'])-START).days
            self.assertEqual(int(y),int(STATES[offset%len(STATES)]=='NMCS'))
            seen_current |= row['current_status']=='NMCS'
        self.assertTrue(seen_current)

    def test_validation_cannot_fit_preprocessing(self):
        bad=copy.copy(self.batch);bad.role='validation'
        with self.assertRaises(ValueError):fit_candidate(bad,CANDIDATES[0])

    def test_missing_hours_dropped_and_unseen_categories_not_fitted(self):
        import numpy as np
        model,info=fit_candidate(self.batch,CANDIDATES[0])
        self.assertIn('hrs_to_insp',info['dropped_all_missing_train_features'])
        self.assertIn('hrs_to_phase',info['dropped_all_missing_train_features'])
        changed=self.batch.frame.copy();changed['command']='FICTIONAL_UNSEEN'
        values=predict(model,changed)
        self.assertTrue(((values>=0)&(values<=1)).all())
        encoder=model.named_steps['preprocess'].named_transformers_['categorical']
        self.assertNotIn('FICTIONAL_UNSEEN',encoder.categories_[1])
        imputer=model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute']
        medians=imputer.statistics_.copy()
        changed_hours=self.batch.frame.copy()
        changed_hours['hrs_to_insp']=99999.;changed_hours['hrs_to_phase']=99999.
        self.assertTrue(np.array_equal(predict(model,self.batch.frame),predict(model,changed_hours)))
        self.assertTrue(np.array_equal(medians,imputer.statistics_,equal_nan=True))

    def test_deterministic_logistic_and_boosted_prediction(self):
        import numpy as np
        configs=[CANDIDATES[0],{**CANDIDATES[2],'max_iter':10,'min_samples_leaf':5}]
        for config in configs:
            with self.subTest(algorithm=config['algorithm']):
                a,_=fit_candidate(self.batch,config);b,_=fit_candidate(self.batch,config)
                p=predict(a,self.batch.frame);q=predict(b,self.batch.frame)
                self.assertTrue(np.array_equal(p,q))
                self.assertTrue(np.isfinite(p).all())

    def test_prediction_rejects_fractional_or_inconsistent_offsets(self):
        model,_=fit_candidate(self.batch,CANDIDATES[0])
        for value in (1.5,181):
            bad=self.batch.frame.copy();bad['horizon_days']=value
            with self.assertRaises(ValueError):predict(model,bad)
        bad=self.batch.frame.copy();bad['log_horizon']=999
        with self.assertRaises(ValueError):predict(model,bad)

    def test_identical_cohort_requires_horizon_metadata_alignment(self):
        bad=copy.deepcopy(self.batch);bad.frame['horizon_days']=1
        with self.assertRaises(ValueError):audit_batch(bad)


if __name__=='__main__':unittest.main()
