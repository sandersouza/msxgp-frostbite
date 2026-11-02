"""The actual banked reader must return every ID and original-derived mask."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


class PresentationGeometryTests(unittest.TestCase):
    def test_partial_wrong_grid_id_pattern_or_error_flag_is_rejected(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_geometry_check'), 'native geometry checker missing')
        api = importlib.import_module('presentation_geometry_check'); expected = bytes(123)
        api.verify_row(expected, expected)
        for offset in (0, 1, 2, 25, 26, 121, 122):
            changed = bytearray(expected); changed[offset] ^= 1
            with self.assertRaises(ValueError): api.verify_row(bytes(changed), expected)
        with self.assertRaises(ValueError): api.verify_row(expected[:-1], expected)
