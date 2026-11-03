"""Persisted measured RGB evidence must be complete, consistent and read-only."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationPaletteTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_palette'), 'RGB measurement checker missing')
        return importlib.import_module('presentation_palette')

    def test_every_observed_pixel_is_measured_and_state_reads_are_unchanged(self):
        api = self.api(); indexed = bytes((0, 90, 104, 186)) * 8400
        rgb = bytes((0, 0, 0, 212, 108, 195, 164, 89, 208, 101, 209, 174)) * 8400
        self.assertEqual(api.sample_palette(indexed, rgb, 186, b'state', b'state'),
                         {0: (0, 0, 0), 90: (212, 108, 195), 104: (164, 89, 208), 186: (101, 209, 174)})
        with self.assertRaisesRegex(ValueError, 'state'): api.sample_palette(indexed, rgb, 186, b'a', b'b')
        with self.assertRaisesRegex(ValueError, 'requested'): api.sample_palette(indexed, rgb, 188, b'a', b'a')
        broken = bytearray(rgb); broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'inconsistent'): api.sample_palette(indexed, bytes(broken), 186, b'a', b'a')
        for image, colors in ((indexed[:-1], rgb), (indexed, rgb[:-1])):
            with self.assertRaises(ValueError): api.sample_palette(image, colors, 186, b'a', b'a')
        with self.assertRaises(ValueError): api.sample_palette(bytes([1]) * 33600, rgb, 1, b'a', b'a')
