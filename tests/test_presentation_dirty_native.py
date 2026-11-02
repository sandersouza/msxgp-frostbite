"""The native state/dirty proof compares every state byte and every row bit."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class DirtyNativeTests(unittest.TestCase):
    def test_native_state_and_dirty_row_record_must_be_complete_and_exact(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_dirty_native_check'),'native dirty-state checker missing')
        api=importlib.import_module('presentation_dirty_native_check');expected=bytes(range(64))+bytes((1,2,4))
        api.verify_row(expected,expected)
        for actual in (expected[:-1],expected+b'\0',expected[:32]+b'\xff'+expected[33:],expected[:-1]+b'\x08'):
            with self.assertRaises(ValueError):api.verify_row(actual,expected)
