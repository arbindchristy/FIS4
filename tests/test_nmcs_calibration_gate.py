from datetime import timedelta
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts import evaluate_nmcs_calibration as gate


class CalibrationGateTests(unittest.TestCase):
    def test_calendar_alone_rules_out_every_fit(self):
        counts = [sum(n >= 3 for n in gate.block_counts(
            gate.grid(start, end - timedelta(days=30)), start).values())
            for _, start, end in gate.FOLDS]
        self.assertEqual(counts, [1, 2, 3])

    def test_reader_stops_before_locked_payload(self):
        row = b'2025-11-20T20:00:00,00001,NMCS,Fictional,UH-60L\n'
        data = gate.HEADER + row
        with tempfile.TemporaryDirectory(dir=gate.TMP) as folder:
            path = Path(folder) / 'events.csv'
            path.write_bytes(data + b'2025-11-21\xff')
            records, fingerprint = gate.prefix(path, gate.END)
            self.assertEqual((records[0].tail, records[0].status), ('00001', 'NMCS'))
            self.assertEqual(fingerprint, hashlib.sha256(data).hexdigest())

    def test_common_targets_and_calendar_purge(self):
        rows = [
            gate.Observation(gate.datetime.combine(gate.START + timedelta(days=i), gate.time()),
                             '00001', status, 'Fictional', 'UH-60L')
            for i, status in [(0, 'NMCS'), (7, 'NMCM'), (30, 'NMCS')]
        ]
        cohort, excluded = gate.cohort(rows, gate.START, gate.START + timedelta(days=30))
        self.assertEqual(len(cohort), 1)
        self.assertEqual([target.value for target in cohort[0][3]], [0, 1])
        self.assertEqual(excluded, {'calendar_purge': 4, 'ineligible_reference': 0,
                                    'missing_target': 0})


if __name__ == '__main__':
    unittest.main()
