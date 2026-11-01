import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class FloeCatalogTests(unittest.TestCase):
    def test_complete_partition_has_no_gap_overlap_or_empty_receipt(self):
        api=importlib.import_module('floe_catalog')
        good=[{'start':0,'stop':80,'cases':80*34*10*160},{'start':80,'stop':160,'cases':80*34*10*160}]
        self.assertEqual(api.validate_partitions(good,10),8704000)
        for invalid in ([],good[:1],[good[0],{**good[1],'start':79}],[{**good[0],'cases':0},good[1]]):
            with self.assertRaises(ValueError):api.validate_partitions(invalid,10)
    def test_lossless_indices_use_full_literal_rows_and_relative_positions(self):
        api=importlib.import_module('floe_catalog')
        rows=[bytes(58),bytes([1])+bytes(57),bytes(58)]
        pool,index=api.intern_rows(rows)
        self.assertEqual(pool,[rows[0],rows[1]]);self.assertEqual(index,[0,1,0])
        with self.assertRaises(ValueError):api.intern_rows([bytes(57)])
