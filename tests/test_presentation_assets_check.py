"""Whole-source pixel comparison cannot accept self-consistent wrong rasters."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationAssetsCheckTests(unittest.TestCase):
    def test_actual_source_pixels_and_all_ram_are_preserved(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_assets_check'), 'source model checker missing')
        api = importlib.import_module('presentation_assets_check')
        ram = [0] * 128; ram[0x3F] = 128  # Explicit original visible blanking.
        original = list(ram)
        self.assertEqual(api.compare_scene(bytes(4096), ram, bytes(33600))['different_pixels'], 0)
        self.assertEqual(ram, original)
        changed = bytearray(33600); changed[-1] = 2
        with self.assertRaisesRegex(ValueError, '1 source pixel'): api.compare_scene(bytes(4096), ram, bytes(changed))
        with self.assertRaises(ValueError): api.compare_scene(bytes(4096), ram, bytes(33599))
