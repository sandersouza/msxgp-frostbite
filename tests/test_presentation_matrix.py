"""A component sequence needs a complete ordered, VBlank-bounded trace."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

class PresentationMatrixTests(unittest.TestCase):
    def test_trace_rejects_missing_reordered_visible_and_nonpositive_measurements(self):
        self.assertIsNotNone(importlib.util.find_spec('presentation_matrix_check'),'actual matrix checker missing')
        api=importlib.import_module('presentation_matrix_check')
        self.assertEqual(api.verify_timing('0 1000 192 194\n1 2000 -12 -10\n',2),2000)
        for rows in ('0 1000 192 194\n','1 1000 192 194\n0 2000 192 194\n','0 1000 191 194\n1 2000 192 194\n','0 1000 192 20\n1 2000 192 194\n','0 0 192 194\n1 2000 192 194\n'):
            with self.assertRaises(ValueError):api.verify_timing(rows,2)
