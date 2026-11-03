"""Actual-Z80 cache result rows must retain full bytes and metadata."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationCacheTests(unittest.TestCase):
    def test_cache_row_rejects_tile_metadata_and_transaction_mutations(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_cache_check'), 'native cache checker missing')
        api = importlib.import_module('presentation_cache_check')
        expected = bytes(6200)
        self.assertIsNone(api.verify_row(expected, expected))
        for offset in (0, 1, 2, 7, 8, 55, 56, 6199):
            actual = bytearray(expected); actual[offset] ^= 1
            with self.assertRaises(ValueError): api.verify_row(bytes(actual), expected)
        for actual in (expected[:-1], expected + b'\0'):
            with self.assertRaises(ValueError): api.verify_row(actual, expected)

    def test_microproof_has_a_bounded_lookup_budget_separate_from_frame_acceptance(self):
        api = importlib.import_module('presentation_cache_check')
        api.verify_cycles([1, 6000])
        for values in ([], [0], [6001], [True]):
            with self.assertRaises(ValueError): api.verify_cycles(values)
