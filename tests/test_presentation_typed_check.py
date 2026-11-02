"""A typed native tile proof rejects incomplete or changed payloads/errors."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PresentationTypedCheckTests(unittest.TestCase):
    def test_complete_native_tile_and_error_flag_must_match(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_typed_check'),'native typed constructor checker missing')
        api=importlib.import_module('presentation_typed_check')
        expected=bytes(range(16))+bytes(1)
        api.verify_row(expected,expected)
        for actual in (expected[:-1],expected+b'\0',expected[:8]+b'\xff'+expected[9:],expected[:-1]+b'\1'):
            with self.assertRaises(ValueError):api.verify_row(actual,expected)
