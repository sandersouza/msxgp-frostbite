"""Every compressed pattern read must retain all eight bytes and error flags."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class TemplateReaderTests(unittest.TestCase):
    def test_full_native_pattern_row_rejects_truncation_bad_error_and_pixel_bytes(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_reader_check'))
        api=importlib.import_module('presentation_template_reader_check');row=bytes((0,0))+bytes(range(8))
        api.verify_row(row,row)
        for actual in (row[:-1],bytes((1,))+row[1:],row[:-1]+bytes((255,))):
            with self.assertRaises(ValueError):api.verify_row(actual,row)
