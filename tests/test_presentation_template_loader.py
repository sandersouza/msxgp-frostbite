"""The native template loader must retain complete keys and NAME programs."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class TemplateLoaderTests(unittest.TestCase):
    def test_full_loader_payload_rejects_missing_or_changed_bytes(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_template_loader_check'))
        api=importlib.import_module('presentation_template_loader_check')
        row=bytes((1,))+bytes(28)+bytes(30)+bytes(2)
        self.assertEqual(len(row),api.ROW_BYTES);api.verify_row(row,row)
        for at in (0,1,28,29,58,59,60):
            bad=bytearray(row);bad[at]^=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
