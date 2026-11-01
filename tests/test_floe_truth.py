import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FloeTruthTests(unittest.TestCase):
    def test_all_literal_view_bounds_and_high_channels(self):
        api=importlib.import_module('floe_truth')
        self.assertEqual(api.view_index(0,0,0),0)
        self.assertEqual(api.view_index(5,18,1),227)
        row=bytearray(58);row[0]=1;row[29+28]=8
        self.assertEqual(api.sample(row,0),135)
        self.assertEqual(api.sample(row,1),7)
        self.assertEqual(api.sample(row,227),71)
        for args in ((6,0,0),(0,19,0),(0,0,2),(-1,0,0)):
            with self.assertRaises(ValueError):api.view_index(*args)

    def test_exact_record_shape_padding_and_complete_fields(self):
        api=importlib.import_module('floe_truth')
        full=bytearray(384);full[232:360]=bytes(range(128));full[360:365]=b'\1\2\3\4\xff'
        decoded=api.full_record(full)
        self.assertEqual(decoded['ram'],bytes(range(128)))
        self.assertEqual(decoded['registers'],{'a':1,'x':2,'y':3,'p':4,'sp':255})
        self.assertEqual(len(decoded['truth']),4)
        for invalid in (full[:-1],full+b'\0'):
            with self.assertRaises(ValueError):api.full_record(invalid)
        full[28]=16
        with self.assertRaises(ValueError):api.full_record(full)

    def test_roi_requires_exact_size_and_original_bus_low_bits(self):
        api=importlib.import_module('floe_truth')
        data=bytearray(78);data[58]=199
        self.assertEqual(api.roi_record(data)['actual'],199)
        data[58]=128
        with self.assertRaises(ValueError):api.roi_record(data)
        with self.assertRaises(ValueError):api.roi_record(data[:-1])
