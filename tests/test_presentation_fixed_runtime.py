"""Fixed-role publication must preserve whole keys, VRAM and both NAME pages."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class FixedRuntimeTests(unittest.TestCase):
    def test_complete_capture_rejects_metadata_pixels_names_and_truncation(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fixed_runtime_check'),'fixed publication proof missing')
        api=importlib.import_module('presentation_fixed_runtime_check');inputs,expected=api.fixtures()
        row=expected[api.ROW_BYTES:api.ROW_BYTES*2]
        api.verify_row(row,row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
        for at in (0,1,2,3,2571,4107,20491,20555):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bad,row)
