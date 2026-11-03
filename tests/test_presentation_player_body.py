"""Player body comparisons use original-space rows, including coarse duplication."""
import importlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class PlayerBodyTests(unittest.TestCase):
    def test_row_origin_and_coarse_duplicate_are_retained(self):
        api=importlib.import_module('presentation_player_body_check')
        rows=[{'y':56,'pattern':128,'color':2}]
        palette={2:5}
        normal=api.planes(rows,False,False,palette)
        coarse=api.planes(rows,False,True,palette)
        self.assertEqual(normal[:3],bytes((1,49,49)))
        self.assertEqual(coarse[:3],bytes((1,49,50)))
        self.assertEqual(normal[7:10],bytes((128,0,0)))
        self.assertEqual(coarse[7:10],bytes((128,128,0)))
        reflected=api.planes(rows,True,True,palette)
        self.assertEqual(reflected[7:9],bytes((1,1)))

    def test_whole_planes_colors_extents_and_fault_are_required(self):
        api=importlib.import_module('presentation_player_body_check');row=bytes(api.ROW_BYTES)
        api.verify_row(row,row)
        for at in (0,1,2,3,6,7,30,102,103):
            bad=bytearray(row);bad[at]=1
            with self.assertRaises(ValueError):api.verify_row(bytes(bad),row)
        with self.assertRaises(ValueError):api.verify_row(row[:-1],row)
