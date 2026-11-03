"""A typed native tile proof rejects incomplete or changed payloads/errors."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PresentationTypedCheckTests(unittest.TestCase):
    def test_igloo_microbudget_requires_native_coverage_and_rejects_slow_tiles(self):
        from presentation_typed_check import verify_igloo_timing
        inputs=(bytes(6)+bytes([5]))*1000
        times=[[i,1900] for i in range(1000)]
        self.assertEqual(verify_igloo_timing(inputs,times)['cases'],1000)
        with self.assertRaises(ValueError):verify_igloo_timing(inputs,times[:-1])
        times[-1][1]=3000
        with self.assertRaises(ValueError):verify_igloo_timing(inputs,times)

    def test_complete_native_tile_and_error_flag_must_match(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_typed_check'),'native typed constructor checker missing')
        api=importlib.import_module('presentation_typed_check')
        expected=bytes(range(16))+bytes(1)
        api.verify_row(expected,expected)
        for actual in (expected[:-1],expected+b'\0',expected[:8]+b'\xff'+expected[9:],expected[:-1]+b'\1'):
            with self.assertRaises(ValueError):api.verify_row(actual,expected)
