"""Exact constructor-key/refcount cache rejects incomplete actual state rows."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationFastCacheTests(unittest.TestCase):
    def test_whole_key_reference_and_pixel_state_is_required(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_fast_cache_check'),'constructor cache microproof missing')
        api=importlib.import_module('presentation_fast_cache_check');row=bytes(8456)
        api.verify_row(row,row)
        for at in (0,1,7,8,391,392,2311,2312,8455):
            changed=bytearray(row);changed[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(changed),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
