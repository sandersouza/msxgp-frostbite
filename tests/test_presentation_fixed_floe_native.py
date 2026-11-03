"""Complete native floe grids must retain exactly the declared cells."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FixedFloeNativeTests(unittest.TestCase):
    def test_complete_grid_payload_rejects_truncation_and_different_retained_bytes(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_floe_native_check'))
        api=importlib.import_module('presentation_fixed_floe_native_check')
        row=bytes((0,))+bytes(64)+bytes([165])*256
        self.assertEqual(len(row),api.ROW_BYTES)
        api.verify_row(row,row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
        changed=bytearray(row);changed[-1]^=1
        with self.assertRaises(ValueError):api.verify_row(bytes(changed),row)

    def test_grid_sorts_deduplicates_and_preserves_unused_id_bytes(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_floe_native_check'))
        api=importlib.import_module('presentation_fixed_floe_native_check')
        initial=bytes([165])*256
        row=api.grid_row({'layers':{(11,3):[{'id':257},{'id':2},{'id':257}]}},88,initial)
        self.assertEqual(row[1+3],2)
        self.assertEqual(row[65+6:65+8],bytes((2,0)))
        self.assertEqual(row[193+6:193+8],bytes((1,1)))
        self.assertEqual(row[-1],165)
        with self.assertRaises(ValueError):api.grid_row({'layers':{(11,3):[{'id':1},{'id':2},{'id':3}]}},88,initial)
