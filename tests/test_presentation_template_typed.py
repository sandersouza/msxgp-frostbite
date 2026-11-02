"""Complete raw-floe constructors need their own native namespace proof."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class TemplateTypedTests(unittest.TestCase):
    def test_complete_tile_carry_and_error_cannot_be_truncated_or_changed(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_typed_check'))
        api=importlib.import_module('presentation_template_typed_check');row=bytes(18)
        api.verify_row(row,row)
        for at in (0,7,8,15,16,17):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
